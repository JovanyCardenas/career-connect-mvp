from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationForm, ApplicationStatusForm, CompanyForm, JobForm, RegisterForm, StudentProfileForm
from .models import Application, Company, Job, SavedJob, StudentProfile, User


def home(request):
    jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")[:6]
    return render(request, "core/home.html", {"jobs": jobs})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        if user.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Your CareerConnect account is ready.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.role == User.Role.STUDENT:
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        context = {
            "profile": profile,
            "applications": request.user.applications.select_related("job", "job__company")[:5],
            "saved_count": request.user.saved_jobs.count(),
            "recommended": Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")[:4],
        }
        return render(request, "core/student_dashboard.html", context)
    if request.user.role == User.Role.EMPLOYER:
        companies = request.user.owned_companies.all()
        jobs = Job.objects.filter(company__owner=request.user).select_related("company")
        return render(request, "core/employer_dashboard.html", {"companies": companies, "jobs": jobs})
    if request.user.role == User.Role.STAFF or request.user.is_superuser:
        return render(request, "core/staff_dashboard.html", {
            "pending_companies": Company.objects.filter(status=Company.Status.PENDING),
            "pending_jobs": Job.objects.filter(status=Job.Status.PENDING).select_related("company"),
            "stats": {
                "students": User.objects.filter(role=User.Role.STUDENT).count(),
                "employers": Company.objects.count(),
                "jobs": Job.objects.filter(status=Job.Status.PUBLISHED).count(),
                "applications": Application.objects.count(),
            },
        })
    return redirect("home")


@login_required
def profile_edit(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Edit student profile", "submit_label": "Save profile"})


def job_list(request):
    jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")
    q = request.GET.get("q", "").strip()
    employment_type = request.GET.get("employment_type", "")
    workplace_type = request.GET.get("workplace_type", "")
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(company__name__icontains=q) | Q(description__icontains=q) | Q(skills__icontains=q) | Q(location__icontains=q))
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)
    if workplace_type:
        jobs = jobs.filter(workplace_type=workplace_type)
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(request.user.saved_jobs.values_list("job_id", flat=True))
    return render(request, "core/job_list.html", {"jobs": jobs, "saved_ids": saved_ids, "employment_choices": Job.EmploymentType.choices, "workplace_choices": Job.WorkplaceType.choices})


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related("company"), pk=pk)
    if job.status != Job.Status.PUBLISHED and not (request.user.is_authenticated and (request.user.is_superuser or request.user.role == User.Role.STAFF or job.created_by == request.user)):
        raise PermissionDenied
    has_applied = request.user.is_authenticated and Application.objects.filter(job=job, student=request.user).exists()
    is_saved = request.user.is_authenticated and SavedJob.objects.filter(job=job, student=request.user).exists()
    return render(request, "core/job_detail.html", {"job": job, "has_applied": has_applied, "is_saved": is_saved})


@login_required
def save_job(request, pk):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    job = get_object_or_404(Job, pk=pk, status=Job.Status.PUBLISHED)
    saved, created = SavedJob.objects.get_or_create(student=request.user, job=job)
    if not created:
        saved.delete()
        messages.info(request, "Job removed from saved jobs.")
    else:
        messages.success(request, "Job saved.")
    return redirect(request.META.get("HTTP_REFERER", job.get_absolute_url()))


@login_required
def saved_jobs(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    saved = request.user.saved_jobs.select_related("job", "job__company")
    return render(request, "core/saved_jobs.html", {"saved": saved})


@login_required
def apply_job(request, pk):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    job = get_object_or_404(Job, pk=pk, status=Job.Status.PUBLISHED)
    if Application.objects.filter(job=job, student=request.user).exists():
        messages.info(request, "You already applied to this job.")
        return redirect(job)
    form = ApplicationForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        application = form.save(commit=False)
        application.job = job
        application.student = request.user
        if not application.resume:
            profile = getattr(request.user, "student_profile", None)
            if profile and profile.resume:
                application.resume = profile.resume
        application.save()
        messages.success(request, "Application submitted successfully.")
        return redirect("my_applications")
    return render(request, "core/form_page.html", {"form": form, "title": f"Apply to {job.title}", "submit_label": "Submit application"})


@login_required
def my_applications(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    return render(request, "core/my_applications.html", {"applications": request.user.applications.select_related("job", "job__company")})


@login_required
def company_create(request):
    if request.user.role != User.Role.EMPLOYER:
        raise PermissionDenied
    form = CompanyForm(request.POST or None)
    if form.is_valid():
        company = form.save(commit=False)
        company.owner = request.user
        company.save()
        messages.success(request, "Company submitted for staff review.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Create company profile", "submit_label": "Submit company"})


@login_required
def job_create(request):
    if request.user.role != User.Role.EMPLOYER:
        raise PermissionDenied
    company = request.user.owned_companies.filter(status=Company.Status.APPROVED).first()
    if not company:
        messages.warning(request, "Your company must be approved before posting jobs.")
        return redirect("dashboard")
    form = JobForm(request.POST or None)
    if form.is_valid():
        job = form.save(commit=False)
        job.company = company
        job.created_by = request.user
        job.status = Job.Status.PENDING
        job.save()
        messages.success(request, "Job submitted for approval.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Post a job", "submit_label": "Submit job for approval"})


@login_required
def employer_applicants(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, company__owner=request.user)
    applications = job.applications.select_related("student", "student__student_profile")
    return render(request, "core/employer_applicants.html", {"job": job, "applications": applications})


@login_required
def application_update(request, pk):
    application = get_object_or_404(Application.objects.select_related("job", "job__company"), pk=pk, job__company__owner=request.user)
    form = ApplicationStatusForm(request.POST or None, instance=application)
    if form.is_valid():
        form.save()
        messages.success(request, "Application status updated.")
        return redirect("employer_applicants", job_pk=application.job_id)
    return render(request, "core/form_page.html", {"form": form, "title": f"Review {application.student}", "submit_label": "Update application"})


@login_required
def moderate_company(request, pk, action):
    if not (request.user.role == User.Role.STAFF or request.user.is_superuser):
        raise PermissionDenied
    company = get_object_or_404(Company, pk=pk)
    company.status = Company.Status.APPROVED if action == "approve" else Company.Status.REJECTED
    company.save(update_fields=["status"])
    messages.success(request, f"Company marked {company.get_status_display().lower()}.")
    return redirect("dashboard")


@login_required
def moderate_job(request, pk, action):
    if not (request.user.role == User.Role.STAFF or request.user.is_superuser):
        raise PermissionDenied
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.PUBLISHED if action == "approve" else Job.Status.REJECTED
    job.save(update_fields=["status"])
    messages.success(request, f"Job marked {job.get_status_display().lower()}.")
    return redirect("dashboard")
