from django.test import TestCase
from django.urls import reverse
from .models import Company, Job, StudentProfile, User

class PlatformSmokeTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student_test", email="student_test@example.com", password="pass12345", role=User.Role.STUDENT)
        StudentProfile.objects.create(user=self.student)
        self.employer = User.objects.create_user(username="employer_test", email="employer_test@example.com", password="pass12345", role=User.Role.EMPLOYER)
        self.company = Company.objects.create(owner=self.employer, name="Test Company", status=Company.Status.APPROVED)
        self.job = Job.objects.create(company=self.company, created_by=self.employer, title="Test Intern", location="Remote", employment_type=Job.EmploymentType.INTERNSHIP, workplace_type=Job.WorkplaceType.REMOTE, description="Test role", status=Job.Status.PUBLISHED)

    def test_home_and_job_pages_load(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("job_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("job_detail", args=[self.job.pk])).status_code, 200)

    def test_student_can_apply(self):
        self.client.login(username="student_test", password="pass12345")
        response = self.client.post(reverse("apply_job", args=[self.job.pk]), {"cover_letter":"I am interested."})
        self.assertRedirects(response, reverse("my_applications"))
        self.assertTrue(self.job.applications.filter(student=self.student).exists())

    def test_employer_dashboard_loads(self):
        self.client.login(username="employer_test", password="pass12345")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
