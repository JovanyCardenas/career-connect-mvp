from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Application, Company, Job, StudentProfile, User


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[(User.Role.STUDENT, "Student"), (User.Role.EMPLOYER, "Employer")])

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "role", "school_name", "password1", "password2"]


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        exclude = ["user"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ["owner", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        exclude = ["company", "created_by", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "requirements": forms.Textarea(attrs={"rows": 5}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter", "resume"]
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 8, "placeholder": "Tell the employer why you are a strong fit..."})}


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status", "employer_notes"]
        widgets = {"employer_notes": forms.Textarea(attrs={"rows": 4})}
