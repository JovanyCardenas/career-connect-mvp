from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Application, Company, Job, SavedJob, StudentProfile, User

admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile)
admin.site.register(Company)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(SavedJob)
