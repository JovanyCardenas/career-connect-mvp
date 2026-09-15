from math import radians, sin, cos, asin, sqrt
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from .forms import (ApplicationForm, ApplicationStatusForm, CompanyForm, JobForm,
                    RegisterForm, StaffApplicationForm, StaffUserForm,
                    StudentDocumentForm, StudentProfileForm, AnnouncementForm, ResumeProfileForm, ResumeExperienceForm, ResumeEducationForm, ResumeAwardForm, ResumeProjectForm)
from .models import (Announcement, Application, Company, Job, SavedJob, StudentDocument, StudentProfile, User, ResumeProfile, ResumeExperience, ResumeEducation, ResumeAward, ResumeProject)

STAFF_ROLES=(User.Role.STAFF,)
KNOWN_CENTERS={
    "santa_maria":(34.9530,-120.4357,"Santa Maria, CA"),
    "san_luis_obispo":(35.2828,-120.6596,"San Luis Obispo, CA"),
    "san_jose":(37.3382,-121.8863,"San Jose, CA"),
}
def is_staff(user): return user.is_authenticated and (user.is_superuser or user.role==User.Role.STAFF)
def haversine(lat1,lon1,lat2,lon2):
    r=3958.8
    dlat=radians(float(lat2)-float(lat1)); dlon=radians(float(lon2)-float(lon1))
    a=sin(dlat/2)**2+cos(radians(float(lat1)))*cos(radians(float(lat2)))*sin(dlon/2)**2
    return 2*r*asin(sqrt(a))

def home(request):
    return render(request,"core/home.html",{"jobs":Job.objects.filter(status=Job.Status.PUBLISHED,is_on_campus=False).select_related("company")[:6]})

def register(request):
    if request.user.is_authenticated:return redirect("dashboard")
    form=RegisterForm(request.POST or None)
    if form.is_valid():
        user=form.save()
        if user.role in (User.Role.STUDENT,User.Role.ALUMNI): StudentProfile.objects.create(user=user)
        login(request,user); messages.success(request,"Your CareerConnect account is ready."); return redirect("dashboard")
    return render(request,"registration/register.html",{"form":form})

@login_required
def dashboard(request):
    if request.user.role in (User.Role.STUDENT,User.Role.ALUMNI):
        p,_=StudentProfile.objects.get_or_create(user=request.user)
        return render(request,"core/student_dashboard.html",{"profile":p,"applications":request.user.applications.select_related("job","job__company")[:5],"saved_count":request.user.saved_jobs.count(),"document_count":request.user.documents.count(),"recommended":Job.objects.filter(status=Job.Status.PUBLISHED).filter(Q(is_on_campus=False)|Q(is_on_campus=True,target_school__iexact=request.user.school_name) if request.user.role==User.Role.STUDENT else Q(is_on_campus=False)).select_related("company").order_by("-is_on_campus","-created_at")[:4]})
    if request.user.role==User.Role.EMPLOYER:
        return render(request,"core/employer_dashboard.html",{"companies":request.user.owned_companies.all(),"jobs":Job.objects.filter(company__owner=request.user).select_related("company")})
    if is_staff(request.user):
        return render(request,"core/staff_dashboard.html",{"pending_companies":Company.objects.filter(status=Company.Status.PENDING),"pending_jobs":Job.objects.filter(status=Job.Status.PENDING).select_related("company"),"stats":{"students":User.objects.filter(role__in=[User.Role.STUDENT,User.Role.ALUMNI]).count(),"employers":User.objects.filter(role=User.Role.EMPLOYER).count(),"jobs":Job.objects.count(),"applications":Application.objects.count()}})
    return redirect("home")

@login_required
def profile_edit(request):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    p,_=StudentProfile.objects.get_or_create(user=request.user)
    form=StudentProfileForm(request.POST or None,instance=p)
    if form.is_valid(): form.save(); messages.success(request,"Profile updated."); return redirect("dashboard")
    return render(request,"core/form_page.html",{"form":form,"title":"Edit student profile","submit_label":"Save profile"})

@login_required
def document_hub(request):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    form=StudentDocumentForm(request.POST or None,request.FILES or None)
    if form.is_valid():
        d=form.save(commit=False); d.student=request.user; d.save(); messages.success(request,"Document uploaded."); return redirect("document_hub")
    return render(request,"core/document_hub.html",{"documents":request.user.documents.order_by("-created_at"),"form":form})

@login_required
def document_delete(request,pk):
    d=get_object_or_404(StudentDocument,pk=pk,student=request.user)
    if request.method=="POST": d.file.delete(save=False); d.delete(); messages.success(request,"Document removed.")
    return redirect("document_hub")

def job_list(request):
    jobs=Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")
    if request.user.is_authenticated and request.user.role==User.Role.STUDENT:
        jobs=jobs.filter(Q(is_on_campus=False)|Q(is_on_campus=True,target_school__iexact=request.user.school_name)).order_by("-is_on_campus","-created_at")
    else:
        jobs=jobs.filter(is_on_campus=False)
    q=request.GET.get("q","").strip()
    filters={"employment_type":request.GET.get("employment_type", ""),"workplace_type":request.GET.get("workplace_type", ""),"experience_level":request.GET.get("experience_level", ""),"degree_required":request.GET.get("degree_required", "")}
    if q: jobs=jobs.filter(Q(title__icontains=q)|Q(company__name__icontains=q)|Q(description__icontains=q)|Q(skills__icontains=q)|Q(location__icontains=q))
    for k,v in filters.items():
        if v: jobs=jobs.filter(**{k:v})
    salary_min=request.GET.get("salary_min","")
    if salary_min.isdigit(): jobs=jobs.filter(Q(salary_max__gte=int(salary_min))|Q(salary_min__gte=int(salary_min)))
    center=request.GET.get("center",""); radius=request.GET.get("radius","")
    distance_map={}
    if center in KNOWN_CENTERS and radius.isdigit():
        lat,lon,_=KNOWN_CENTERS[center]; maxm=float(radius); ids=[]
        for j in jobs:
            if j.workplace_type==Job.WorkplaceType.REMOTE: ids.append(j.pk); distance_map[j.pk]=0
            elif j.latitude is not None and j.longitude is not None:
                d=haversine(lat,lon,j.latitude,j.longitude)
                if d<=maxm: ids.append(j.pk); distance_map[j.pk]=round(d,1)
        jobs=jobs.filter(pk__in=ids)
    saved_ids=set(request.user.saved_jobs.values_list("job_id",flat=True)) if request.user.is_authenticated else set()
    return render(request,"core/job_list.html",{"jobs":jobs,"saved_ids":saved_ids,"distance_map":distance_map,"employment_choices":Job.EmploymentType.choices,"workplace_choices":Job.WorkplaceType.choices,"experience_choices":Job.ExperienceLevel.choices,"degree_choices":Job.DegreeRequired.choices,"centers":KNOWN_CENTERS})

def job_detail(request,pk):
    job=get_object_or_404(Job.objects.select_related("company"),pk=pk)
    privileged=is_staff(request.user) or (request.user.is_authenticated and job.company.owner==request.user)
    if job.status!=Job.Status.PUBLISHED and not privileged: raise PermissionDenied
    if job.is_on_campus and not privileged and not (request.user.is_authenticated and request.user.role==User.Role.STUDENT and request.user.school_name.lower()==job.target_school.lower()): raise PermissionDenied
    return render(request,"core/job_detail.html",{"job":job,"has_applied":request.user.is_authenticated and Application.objects.filter(job=job,student=request.user).exists(),"is_saved":request.user.is_authenticated and SavedJob.objects.filter(job=job,student=request.user).exists()})

@login_required
def save_job(request,pk):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    job=get_object_or_404(Job,pk=pk,status=Job.Status.PUBLISHED); obj,created=SavedJob.objects.get_or_create(student=request.user,job=job)
    if not created: obj.delete(); messages.info(request,"Job removed from saved jobs.")
    else: messages.success(request,"Job saved.")
    return redirect(request.META.get("HTTP_REFERER",job.get_absolute_url()))

@login_required
def saved_jobs(request):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    return render(request,"core/saved_jobs.html",{"saved":request.user.saved_jobs.select_related("job","job__company")})

@login_required
def apply_job(request,pk):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    job=get_object_or_404(Job,pk=pk,status=Job.Status.PUBLISHED)
    if job.is_on_campus and not (request.user.role==User.Role.STUDENT and request.user.school_name.lower()==job.target_school.lower()): raise PermissionDenied
    if Application.objects.filter(job=job,student=request.user).exists(): messages.info(request,"You already applied to this job."); return redirect(job)
    form=ApplicationForm(request.POST or None,user=request.user)
    if form.is_valid():
        a=form.save(commit=False); a.job=job; a.student=request.user; a.save(); messages.success(request,"Application submitted successfully."); return redirect("my_applications")
    return render(request,"core/form_page.html",{"form":form,"title":f"Apply to {job.title}","submit_label":"Submit application","help_text":"Upload résumés and cover letters first in the Document Hub."})

@login_required
def my_applications(request):
    if request.user.role not in (User.Role.STUDENT,User.Role.ALUMNI): raise PermissionDenied
    return render(request,"core/my_applications.html",{"applications":request.user.applications.select_related("job","job__company")})

@login_required
def company_create(request):
    if request.user.role!=User.Role.EMPLOYER: raise PermissionDenied
    form=CompanyForm(request.POST or None)
    if form.is_valid(): c=form.save(commit=False); c.owner=request.user; c.save(); messages.success(request,"Company submitted for staff review."); return redirect("dashboard")
    return render(request,"core/form_page.html",{"form":form,"title":"Create company profile","submit_label":"Submit company"})

@login_required
def company_edit(request,pk):
    company=get_object_or_404(Company,pk=pk)
    if company.owner!=request.user and not is_staff(request.user): raise PermissionDenied
    form=CompanyForm(request.POST or None,instance=company)
    if form.is_valid():
        c=form.save(commit=False)
        if not is_staff(request.user): c.status=Company.Status.PENDING
        c.save(); messages.success(request,"Company updated"+("." if is_staff(request.user) else " and returned for staff review.")); return redirect("dashboard" if not is_staff(request.user) else "staff_companies")
    return render(request,"core/form_page.html",{"form":form,"title":"Edit company","submit_label":"Save company"})

@login_required
def job_create(request):
    if request.user.role!=User.Role.EMPLOYER: raise PermissionDenied
    if not request.user.owned_companies.filter(status=Company.Status.APPROVED).exists(): messages.warning(request,"You need an approved company before posting jobs."); return redirect("dashboard")
    form=JobForm(request.POST or None,user=request.user)
    if form.is_valid(): j=form.save(commit=False); j.created_by=request.user; j.status=Job.Status.PENDING; j.save(); messages.success(request,"Job submitted for approval."); return redirect("dashboard")
    return render(request,"core/form_page.html",{"form":form,"title":"Post a job","submit_label":"Submit job for approval"})

@login_required
def job_edit(request,pk):
    job=get_object_or_404(Job,pk=pk)
    staff=is_staff(request.user)
    if not staff and job.company.owner!=request.user: raise PermissionDenied
    form=JobForm(request.POST or None,instance=job,user=request.user,staff=staff)
    if form.is_valid():
        j=form.save(commit=False)
        if not staff: j.status=Job.Status.PENDING; j.review_notes=""
        j.save(); messages.success(request,"Job updated"+("." if staff else " and sent to staff for review.")); return redirect("staff_jobs" if staff else "dashboard")
    return render(request,"core/form_page.html",{"form":form,"title":"Edit job posting","submit_label":"Save changes"})

@login_required
def employer_applicants(request,job_pk):
    job=get_object_or_404(Job,pk=job_pk,company__owner=request.user)
    return render(request,"core/employer_applicants.html",{"job":job,"applications":job.applications.select_related("student","student__student_profile","resume_document","cover_letter_document")})

@login_required
def application_detail(request,pk):
    a=get_object_or_404(Application.objects.select_related("job","job__company","student","student__student_profile","resume_document","cover_letter_document"),pk=pk)
    if not (is_staff(request.user) or a.job.company.owner==request.user or a.student==request.user): raise PermissionDenied
    return render(request,"core/application_detail.html",{"application":a,"profile":a.student.student_profile})

@login_required
def application_update(request,pk):
    a=get_object_or_404(Application.objects.select_related("job","job__company"),pk=pk,job__company__owner=request.user)
    form=ApplicationStatusForm(request.POST or None,instance=a)
    if form.is_valid(): form.save(); messages.success(request,"Application status updated."); return redirect("application_detail",pk=a.pk)
    return render(request,"core/form_page.html",{"form":form,"title":f"Review {a.student}","submit_label":"Update application"})

@login_required
def staff_students(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=User.objects.filter(role__in=[User.Role.STUDENT,User.Role.ALUMNI]).select_related("student_profile"); q=request.GET.get("q","").strip();
    if q: qs=qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(username__icontains=q)|Q(personal_email__icontains=q)|Q(school_email__icontains=q)|Q(student_id__icontains=q))
    return render(request,"core/staff_users.html",{"title":"Students and alumni","users":qs,"kind":"student","q":q})

@login_required
def staff_student_detail(request,pk):
    if not is_staff(request.user): raise PermissionDenied
    student=get_object_or_404(User,pk=pk,role__in=[User.Role.STUDENT,User.Role.ALUMNI])
    profile,_=StudentProfile.objects.get_or_create(user=student)
    return render(request,"core/staff_student_detail.html",{"student":student,"profile":profile,"documents":student.documents.all(),"applications":student.applications.select_related("job","job__company")})

@login_required
def staff_employers(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=User.objects.filter(role=User.Role.EMPLOYER); q=request.GET.get("q","").strip();
    if q: qs=qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(username__icontains=q)|Q(personal_email__icontains=q)|Q(email__icontains=q))
    return render(request,"core/staff_users.html",{"title":"Registered employers","users":qs,"kind":"employer","q":q})
@login_required
def staff_user_edit(request,pk):
    if not is_staff(request.user): raise PermissionDenied
    u=get_object_or_404(User,pk=pk); form=StaffUserForm(request.POST or None,instance=u)
    if form.is_valid(): form.save(); messages.success(request,"Account updated."); return redirect("staff_students" if u.role in (User.Role.STUDENT,User.Role.ALUMNI) else ("staff_guests" if u.role==User.Role.GUEST else "staff_employers"))
    return render(request,"core/form_page.html",{"form":form,"title":f"Edit {u}","submit_label":"Save account"})
@login_required
def staff_send_reset(request,pk):
    if not is_staff(request.user): raise PermissionDenied
    u=get_object_or_404(User,pk=pk)
    PasswordResetForm({"email":u.email}).save(request=request,use_https=request.is_secure(),email_template_name="registration/password_reset_email.html")
    messages.success(request,f"Password reset instructions sent to {u.email}."); return redirect(request.META.get("HTTP_REFERER","dashboard"))
@login_required
def staff_companies(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=Company.objects.select_related("owner"); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(name__icontains=q)|Q(industry__icontains=q)|Q(location__icontains=q)|Q(owner__username__icontains=q)|Q(owner__personal_email__icontains=q))
    return render(request,"core/staff_companies.html",{"companies":qs,"q":q})
@login_required
def staff_jobs(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=Job.objects.select_related("company","created_by"); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(title__icontains=q)|Q(company__name__icontains=q)|Q(location__icontains=q)|Q(skills__icontains=q)|Q(target_school__icontains=q))
    return render(request,"core/staff_jobs.html",{"jobs":qs,"q":q})
@login_required
def staff_applications(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=Application.objects.select_related("student","job","job__company"); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(student__first_name__icontains=q)|Q(student__last_name__icontains=q)|Q(student__student_id__icontains=q)|Q(student__personal_email__icontains=q)|Q(job__title__icontains=q)|Q(job__company__name__icontains=q))
    return render(request,"core/staff_applications.html",{"applications":qs,"q":q})
@login_required
def staff_application_review(request,pk):
    if not is_staff(request.user): raise PermissionDenied
    a=get_object_or_404(Application,pk=pk); form=StaffApplicationForm(request.POST or None,instance=a)
    if form.is_valid(): form.save(); messages.success(request,"Application review updated."); return redirect("staff_applications")
    return render(request,"core/form_page.html",{"form":form,"title":"Staff application review","submit_label":"Save review"})

@login_required
def moderate_company(request,pk,action):
    if not is_staff(request.user): raise PermissionDenied
    c=get_object_or_404(Company,pk=pk); c.status=Company.Status.APPROVED if action=="approve" else Company.Status.REJECTED; c.save(update_fields=["status"]); messages.success(request,f"Company marked {c.get_status_display().lower()}."); return redirect(request.META.get("HTTP_REFERER","dashboard"))
@login_required
def moderate_job(request,pk,action):
    if not is_staff(request.user): raise PermissionDenied
    j=get_object_or_404(Job,pk=pk)
    mapping={"approve":Job.Status.PUBLISHED,"reject":Job.Status.REJECTED,"unpublish":Job.Status.UNPUBLISHED,"close":Job.Status.CLOSED}
    if action not in mapping: raise PermissionDenied
    j.status=mapping[action]; j.save(update_fields=["status"]); messages.success(request,f"Job marked {j.get_status_display().lower()}."); return redirect(request.META.get("HTTP_REFERER","dashboard"))

@login_required
def staff_guests(request):
    if not is_staff(request.user): raise PermissionDenied
    qs=User.objects.filter(role=User.Role.GUEST); q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(username__icontains=q)|Q(personal_email__icontains=q))
    return render(request,"core/staff_users.html",{"title":"Community guests","users":qs,"kind":"guest","q":q})

@login_required
def staff_announcements(request):
    if not is_staff(request.user): raise PermissionDenied
    q=request.GET.get("q","").strip(); qs=Announcement.objects.all()
    if q: qs=qs.filter(Q(title__icontains=q)|Q(message__icontains=q)|Q(school_name__icontains=q))
    return render(request,"core/staff_announcements.html",{"announcements":qs,"q":q})
@login_required
def announcement_edit(request,pk=None):
    if not is_staff(request.user): raise PermissionDenied
    obj=get_object_or_404(Announcement,pk=pk) if pk else None; form=AnnouncementForm(request.POST or None,request.FILES or None,instance=obj)
    if form.is_valid(): a=form.save(commit=False); a.created_by=request.user; a.save(); messages.success(request,"Announcement saved."); return redirect("staff_announcements")
    return render(request,"core/form_page.html",{"form":form,"title":"Edit announcement" if obj else "New announcement","submit_label":"Save announcement"})
@login_required
def announcement_delete(request,pk):
    if not is_staff(request.user): raise PermissionDenied
    a=get_object_or_404(Announcement,pk=pk)
    if request.method=="POST": a.delete(); messages.success(request,"Announcement removed.")
    return redirect("staff_announcements")

RESUME_MODELS={"experience":(ResumeExperience,ResumeExperienceForm),"education":(ResumeEducation,ResumeEducationForm),"award":(ResumeAward,ResumeAwardForm),"project":(ResumeProject,ResumeProjectForm)}
def resume_user_allowed(user): return user.role in (User.Role.STUDENT,User.Role.ALUMNI)
@login_required
def resume_list(request):
    if not resume_user_allowed(request.user): raise PermissionDenied
    return render(request,"core/resume_list.html",{"resumes":request.user.resume_profiles.all()})
@login_required
def resume_edit(request,pk=None):
    if not resume_user_allowed(request.user): raise PermissionDenied
    r=get_object_or_404(ResumeProfile,pk=pk,student=request.user) if pk else None; form=ResumeProfileForm(request.POST or None,instance=r)
    if form.is_valid(): x=form.save(commit=False); x.student=request.user; x.save(); messages.success(request,"Resume profile saved."); return redirect("resume_detail",pk=x.pk)
    return render(request,"core/form_page.html",{"form":form,"title":"Edit resume profile" if r else "Create resume profile","submit_label":"Save and continue","skill_suggestions":["Python","Java","Django","JavaScript","HTML","CSS","SQL","Git","Customer service","Microsoft Office","Communication","Leadership","Project management","Welding","Bilingual"]})
@login_required
def resume_detail(request,pk):
    r=get_object_or_404(ResumeProfile,pk=pk,student=request.user)
    return render(request,"core/resume_detail.html",{"resume":r})
@login_required
def resume_section_edit(request,pk,kind,item_pk=None):
    r=get_object_or_404(ResumeProfile,pk=pk,student=request.user)
    if kind not in RESUME_MODELS: raise PermissionDenied
    model,formclass=RESUME_MODELS[kind]; obj=get_object_or_404(model,pk=item_pk,resume=r) if item_pk else None; form=formclass(request.POST or None,instance=obj)
    if form.is_valid(): x=form.save(commit=False); x.resume=r; x.save(); messages.success(request,f"Resume {kind} saved."); return redirect("resume_detail",pk=r.pk)
    return render(request,"core/form_page.html",{"form":form,"title":f"{'Edit' if obj else 'Add'} {kind}","submit_label":"Save"})
@login_required
def resume_section_delete(request,pk,kind,item_pk):
    r=get_object_or_404(ResumeProfile,pk=pk,student=request.user)
    if kind not in RESUME_MODELS: raise PermissionDenied
    model,_=RESUME_MODELS[kind]; obj=get_object_or_404(model,pk=item_pk,resume=r)
    if request.method=="POST": obj.delete(); messages.success(request,"Resume item removed.")
    return redirect("resume_detail",pk=r.pk)
@login_required
def resume_export(request,pk,fmt):
    from .resume_exports import build_docx,build_pdf,save_to_hub
    r=get_object_or_404(ResumeProfile,pk=pk,student=request.user)
    if fmt=="pdf": data=build_pdf(request.user,r); ctype="application/pdf"
    elif fmt=="docx": data=build_docx(request.user,r); ctype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else: raise PermissionDenied
    save_to_hub(request.user,r,fmt,data)
    response=HttpResponse(data,content_type=ctype); response["Content-Disposition"]=f'attachment; filename="{r.name.replace(" ","_")}.{fmt}"'; return response
