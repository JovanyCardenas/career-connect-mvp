from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
admin.site.register(User,UserAdmin)
for model in [StudentProfile,StudentDocument,Company,Job,SavedJob,Application,Announcement,ResumeProfile,ResumeExperience,ResumeEducation,ResumeAward,ResumeProject]:
    admin.site.register(model)
