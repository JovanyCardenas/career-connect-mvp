from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from .models import Application, Company, Job, StudentDocument, StudentProfile, User

class PlatformSmokeTests(TestCase):
    def setUp(self):
        self.student=User.objects.create_user(username="student_test",email="student_test@example.com",password="pass12345",role=User.Role.STUDENT)
        StudentProfile.objects.create(user=self.student,major="Software Engineering")
        self.resume=StudentDocument.objects.create(student=self.student,title="Test Resume",kind=StudentDocument.Kind.RESUME,file=SimpleUploadedFile("resume.pdf",b"test",content_type="application/pdf"))
        self.employer=User.objects.create_user(username="employer_test",email="employer_test@example.com",password="pass12345",role=User.Role.EMPLOYER)
        self.staff=User.objects.create_user(username="staff_test",email="staff_test@example.com",password="pass12345",role=User.Role.STAFF)
        self.company=Company.objects.create(owner=self.employer,name="Test Company",status=Company.Status.APPROVED)
        self.company2=Company.objects.create(owner=self.employer,name="Second Company",status=Company.Status.APPROVED)
        self.job=Job.objects.create(company=self.company,created_by=self.employer,title="Test Intern",location="Santa Maria, CA",latitude=34.9530,longitude=-120.4357,employment_type=Job.EmploymentType.INTERNSHIP,workplace_type=Job.WorkplaceType.ONSITE,description="Test role",status=Job.Status.PUBLISHED)
    def test_home_and_job_pages_load(self):
        self.assertEqual(self.client.get(reverse("home")).status_code,200)
        self.assertEqual(self.client.get(reverse("job_list")).status_code,200)
        self.assertEqual(self.client.get(reverse("job_detail",args=[self.job.pk])).status_code,200)
    def test_student_can_apply_with_document(self):
        self.client.login(username="student_test",password="pass12345")
        response=self.client.post(reverse("apply_job",args=[self.job.pk]),{"resume_document":self.resume.pk,"cover_letter_text":"Interested"})
        self.assertRedirects(response,reverse("my_applications")); self.assertTrue(self.job.applications.filter(student=self.student).exists())
    def test_employer_selects_company_and_edits_job_to_pending(self):
        self.client.login(username="employer_test",password="pass12345")
        data={"company":self.company2.pk,"title":"Updated Job","location":"Remote","employment_type":Job.EmploymentType.FULL_TIME,"workplace_type":Job.WorkplaceType.REMOTE,"experience_level":Job.ExperienceLevel.ENTRY,"degree_required":Job.DegreeRequired.NONE,"description":"Updated"}
        self.client.post(reverse("job_edit",args=[self.job.pk]),data)
        self.job.refresh_from_db(); self.assertEqual(self.job.company,self.company2); self.assertEqual(self.job.status,Job.Status.PENDING)
    def test_staff_management_pages_load(self):
        self.client.login(username="staff_test",password="pass12345")
        for name in ["staff_students","staff_employers","staff_companies","staff_jobs","staff_applications"]: self.assertEqual(self.client.get(reverse(name)).status_code,200)
