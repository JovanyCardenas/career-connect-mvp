from django.urls import path
from . import views
urlpatterns=[
path("",views.home,name="home"),path("register/",views.register,name="register"),path("dashboard/",views.dashboard,name="dashboard"),
path("profile/edit/",views.profile_edit,name="profile_edit"),path("documents/",views.document_hub,name="document_hub"),path("documents/<int:pk>/delete/",views.document_delete,name="document_delete"),
path("jobs/",views.job_list,name="job_list"),path("jobs/<int:pk>/",views.job_detail,name="job_detail"),path("jobs/<int:pk>/save/",views.save_job,name="save_job"),path("jobs/<int:pk>/apply/",views.apply_job,name="apply_job"),
path("saved-jobs/",views.saved_jobs,name="saved_jobs"),path("applications/",views.my_applications,name="my_applications"),path("applications/<int:pk>/",views.application_detail,name="application_detail"),
path("employer/company/new/",views.company_create,name="company_create"),path("companies/<int:pk>/edit/",views.company_edit,name="company_edit"),path("employer/jobs/new/",views.job_create,name="job_create"),path("jobs/<int:pk>/edit/",views.job_edit,name="job_edit"),
path("employer/jobs/<int:job_pk>/applicants/",views.employer_applicants,name="employer_applicants"),path("employer/applications/<int:pk>/update/",views.application_update,name="application_update"),
path("staff/students/",views.staff_students,name="staff_students"),path("staff/students/<int:pk>/",views.staff_student_detail,name="staff_student_detail"),path("staff/employers/",views.staff_employers,name="staff_employers"),path("staff/users/<int:pk>/edit/",views.staff_user_edit,name="staff_user_edit"),path("staff/users/<int:pk>/password-reset/",views.staff_send_reset,name="staff_send_reset"),
path("staff/companies/",views.staff_companies,name="staff_companies"),path("staff/jobs/",views.staff_jobs,name="staff_jobs"),path("staff/applications/",views.staff_applications,name="staff_applications"),path("staff/applications/<int:pk>/review/",views.staff_application_review,name="staff_application_review"),
path("staff/companies/<int:pk>/<str:action>/",views.moderate_company,name="moderate_company"),path("staff/jobs/<int:pk>/<str:action>/",views.moderate_job,name="moderate_job")]
