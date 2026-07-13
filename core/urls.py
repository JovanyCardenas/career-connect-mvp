from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/save/", views.save_job, name="save_job"),
    path("jobs/<int:pk>/apply/", views.apply_job, name="apply_job"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs"),
    path("applications/", views.my_applications, name="my_applications"),
    path("employer/company/new/", views.company_create, name="company_create"),
    path("employer/jobs/new/", views.job_create, name="job_create"),
    path("employer/jobs/<int:job_pk>/applicants/", views.employer_applicants, name="employer_applicants"),
    path("employer/applications/<int:pk>/update/", views.application_update, name="application_update"),
    path("staff/companies/<int:pk>/<str:action>/", views.moderate_company, name="moderate_company"),
    path("staff/jobs/<int:pk>/<str:action>/", views.moderate_job, name="moderate_job"),
]
