from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Application, Company, Job, StudentDocument, StudentProfile, User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[(User.Role.STUDENT,"Student"),(User.Role.EMPLOYER,"Employer")])
    class Meta:
        model=User; fields=["first_name","last_name","username","email","role","school_name","password1","password2"]

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model=StudentProfile; exclude=["user"]; widgets={"bio":forms.Textarea(attrs={"rows":5})}

class StudentDocumentForm(forms.ModelForm):
    class Meta: model=StudentDocument; fields=["title","kind","file"]

class CompanyForm(forms.ModelForm):
    class Meta:
        model=Company; exclude=["owner","status","review_notes"]; widgets={"description":forms.Textarea(attrs={"rows":5})}

class JobForm(forms.ModelForm):
    company = forms.ModelChoiceField(queryset=Company.objects.none())
    class Meta:
        model=Job
        exclude=["created_by","status","review_notes"]
        widgets={"description":forms.Textarea(attrs={"rows":8}),"requirements":forms.Textarea(attrs={"rows":5}),"application_deadline":forms.DateInput(attrs={"type":"date"})}
    def __init__(self,*args,user=None,staff=False,**kwargs):
        super().__init__(*args,**kwargs)
        if staff: self.fields["company"].queryset=Company.objects.all()
        elif user: self.fields["company"].queryset=user.owned_companies.filter(status=Company.Status.APPROVED)

class ApplicationForm(forms.ModelForm):
    class Meta:
        model=Application; fields=["resume_document","cover_letter_document","cover_letter_text"]
        widgets={"cover_letter_text":forms.Textarea(attrs={"rows":7,"placeholder":"Optional note if you are not attaching a cover letter."})}
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        docs=StudentDocument.objects.filter(student=user) if user else StudentDocument.objects.none()
        self.fields["resume_document"].queryset=docs.filter(kind=StudentDocument.Kind.RESUME)
        self.fields["cover_letter_document"].queryset=docs.filter(kind=StudentDocument.Kind.COVER_LETTER)
        self.fields["resume_document"].required=True

class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model=Application; fields=["status","employer_notes"]; widgets={"employer_notes":forms.Textarea(attrs={"rows":4})}

class StaffApplicationForm(forms.ModelForm):
    class Meta:
        model=Application; fields=["status","staff_feedback"]; widgets={"staff_feedback":forms.Textarea(attrs={"rows":5})}

class StaffUserForm(forms.ModelForm):
    class Meta: model=User; fields=["first_name","last_name","username","email","school_name","is_active"]
