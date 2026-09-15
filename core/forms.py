from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import (Announcement, Application, Company, Job, ResumeAward,
    ResumeEducation, ResumeExperience, ResumeProfile, ResumeProject,
    StudentDocument, StudentProfile, User)

class RegisterForm(UserCreationForm):
    account_type = forms.ChoiceField(label="I am creating an account as", choices=[
        (User.Role.STUDENT,"Current student"),(User.Role.EMPLOYER,"Employer"),
        (User.Role.ALUMNI,"Alumni"),(User.Role.GUEST,"Community guest")])
    personal_email = forms.EmailField(label="Personal email")
    school_email = forms.EmailField(required=False)
    student_id = forms.CharField(required=False, label="Student ID number")
    graduation_year = forms.IntegerField(required=False, min_value=1950, max_value=2100)
    class Meta:
        model=User
        fields=["account_type","first_name","last_name","username","personal_email","school_email","student_id","school_name","graduation_year","password1","password2"]
    def clean(self):
        c=super().clean(); role=c.get("account_type")
        if role==User.Role.STUDENT:
            for field in ("student_id","school_email","school_name"):
                if not c.get(field): self.add_error(field,"This field is required for current students.")
        if role==User.Role.ALUMNI and not c.get("graduation_year"):
            self.add_error("graduation_year","Enter the year you graduated.")
        return c
    def save(self,commit=True):
        u=super().save(commit=False); u.role=self.cleaned_data["account_type"]
        u.personal_email=self.cleaned_data["personal_email"]; u.email=u.personal_email
        u.school_email=self.cleaned_data.get("school_email",""); u.student_id=self.cleaned_data.get("student_id","")
        u.school_name=self.cleaned_data.get("school_name",""); u.graduation_year=self.cleaned_data.get("graduation_year")
        if commit: u.save()
        return u

class StudentProfileForm(forms.ModelForm):
    class Meta: model=StudentProfile; exclude=["user"]; widgets={"bio":forms.Textarea(attrs={"rows":5})}
class StudentDocumentForm(forms.ModelForm):
    class Meta: model=StudentDocument; fields=["title","kind","file"]
class CompanyForm(forms.ModelForm):
    class Meta:
        model=Company; exclude=["owner","status","review_notes"]
        widgets={"description":forms.Textarea(attrs={"rows":5})}

class JobForm(forms.ModelForm):
    company=forms.ModelChoiceField(queryset=Company.objects.none())
    class Meta:
        model=Job
        exclude=["created_by","status","review_notes","location","latitude","longitude"]
        widgets={"description":forms.Textarea(attrs={"rows":8}),"requirements":forms.Textarea(attrs={"rows":5}),"application_deadline":forms.DateInput(attrs={"type":"date"}),"address":forms.TextInput(attrs={"placeholder":"Street address (optional)"}),"city":forms.TextInput(attrs={"placeholder":"Santa Maria"}),"state":forms.TextInput(attrs={"placeholder":"CA","maxlength":"2"}),"zip_code":forms.TextInput(attrs={"placeholder":"93454"})}
    def __init__(self,*args,user=None,staff=False,**kwargs):
        super().__init__(*args,**kwargs); self.user=user; self.staff=staff
        self.fields["company"].queryset=Company.objects.all() if staff else (user.owned_companies.filter(status=Company.Status.APPROVED) if user else Company.objects.none())
    def clean(self):
        from .geocoding import geocode_job_location
        c=super().clean(); workplace=c.get("workplace_type"); city=c.get("city",""); z=c.get("zip_code",""); address=c.get("address",""); state=c.get("state","")
        company=c.get("company"); oncampus=c.get("is_on_campus"); school=(c.get("target_school") or "").strip()
        self._geocode_result=None
        if oncampus:
            if not company or not company.is_college: self.add_error("is_on_campus","On-campus jobs must be posted by a company marked as a college.")
            if not school: self.add_error("target_school","Choose the college whose current students can see this job.")
        else: c["target_school"]=""
        if workplace in (Job.WorkplaceType.ONSITE,Job.WorkplaceType.HYBRID) and not city and not z: raise ValidationError("On-site and hybrid jobs require at least a city or ZIP code.")
        if workplace != Job.WorkplaceType.REMOTE or city or z or address:
            self._geocode_result=geocode_job_location(address=address,city=city,state=state,zip_code=z)
            if not self._geocode_result and workplace in (Job.WorkplaceType.ONSITE,Job.WorkplaceType.HYBRID): raise ValidationError("We could not locate this address. Check the city/state or ZIP code and try again.")
        return c
    def save(self,commit=True):
        j=super().save(commit=False); j.refresh_location_label(); r=getattr(self,"_geocode_result",None)
        if r: j.latitude=r.latitude; j.longitude=r.longitude
        elif j.workplace_type==Job.WorkplaceType.REMOTE: j.latitude=j.longitude=None
        if commit: j.save(); self.save_m2m()
        return j

class ApplicationForm(forms.ModelForm):
    class Meta: model=Application; fields=["resume_document","cover_letter_document","cover_letter_text"]; widgets={"cover_letter_text":forms.Textarea(attrs={"rows":7,"placeholder":"Optional note"})}
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs); docs=StudentDocument.objects.filter(student=user) if user else StudentDocument.objects.none(); self.fields["resume_document"].queryset=docs.filter(kind=StudentDocument.Kind.RESUME); self.fields["cover_letter_document"].queryset=docs.filter(kind=StudentDocument.Kind.COVER_LETTER); self.fields["resume_document"].required=True
class ApplicationStatusForm(forms.ModelForm):
    class Meta: model=Application; fields=["status","employer_notes"]; widgets={"employer_notes":forms.Textarea(attrs={"rows":4})}
class StaffApplicationForm(forms.ModelForm):
    class Meta: model=Application; fields=["status","staff_feedback"]; widgets={"staff_feedback":forms.Textarea(attrs={"rows":5})}
class StaffUserForm(forms.ModelForm):
    class Meta: model=User; fields=["first_name","last_name","username","personal_email","school_email","student_id","school_name","graduation_year","is_active"]
    def save(self,commit=True):
        u=super().save(commit=False); u.email=u.personal_email
        if commit:u.save()
        return u
class AnnouncementForm(forms.ModelForm):
    class Meta: model=Announcement; exclude=["created_by"]; widgets={"message":forms.Textarea(attrs={"rows":5}),"starts_at":forms.DateTimeInput(attrs={"type":"datetime-local"}),"ends_at":forms.DateTimeInput(attrs={"type":"datetime-local"})}
class ResumeProfileForm(forms.ModelForm):
    class Meta: model=ResumeProfile; exclude=["student"]; widgets={"objective":forms.Textarea(attrs={"rows":4}),"skills":forms.Textarea(attrs={"rows":3,"list":"skill-suggestions","placeholder":"Python, customer service, welding..."})}
class ResumeExperienceForm(forms.ModelForm):
    class Meta: model=ResumeExperience; exclude=["resume","sort_order"]; widgets={"summary":forms.Textarea(attrs={"rows":4})}
class ResumeEducationForm(forms.ModelForm):
    class Meta: model=ResumeEducation; exclude=["resume","sort_order"]; widgets={"description":forms.Textarea(attrs={"rows":3})}
class ResumeAwardForm(forms.ModelForm):
    class Meta: model=ResumeAward; exclude=["resume","sort_order"]; widgets={"description":forms.Textarea(attrs={"rows":3})}
class ResumeProjectForm(forms.ModelForm):
    class Meta: model=ResumeProject; exclude=["resume","sort_order"]; widgets={"description":forms.Textarea(attrs={"rows":3})}
