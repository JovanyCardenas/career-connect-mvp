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
        self.job=Job.objects.create(company=self.company,created_by=self.employer,title="Test Intern",location="Santa Maria, CA",city="Santa Maria",state="CA",zip_code="93454",latitude=34.9530,longitude=-120.4357,employment_type=Job.EmploymentType.INTERNSHIP,workplace_type=Job.WorkplaceType.ONSITE,description="Test role",status=Job.Status.PUBLISHED)
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
        data={"company":self.company2.pk,"title":"Updated Job","address":"","city":"","state":"","zip_code":"","employment_type":Job.EmploymentType.FULL_TIME,"workplace_type":Job.WorkplaceType.REMOTE,"experience_level":Job.ExperienceLevel.ENTRY,"degree_required":Job.DegreeRequired.NONE,"description":"Updated"}
        self.client.post(reverse("job_edit",args=[self.job.pk]),data)
        self.job.refresh_from_db(); self.assertEqual(self.job.company,self.company2); self.assertEqual(self.job.status,Job.Status.PENDING)
    def test_staff_management_pages_load(self):
        self.client.login(username="staff_test",password="pass12345")
        for name in ["staff_students","staff_employers","staff_companies","staff_jobs","staff_applications"]: self.assertEqual(self.client.get(reverse(name)).status_code,200)

    def test_job_form_geocodes_city_without_exposing_coordinates(self):
        from .forms import JobForm
        data={"company":self.company.pk,"title":"Local Role","address":"","city":"Santa Maria","state":"CA","zip_code":"","employment_type":Job.EmploymentType.FULL_TIME,"workplace_type":Job.WorkplaceType.ONSITE,"experience_level":Job.ExperienceLevel.ENTRY,"degree_required":Job.DegreeRequired.NONE,"description":"Local work"}
        form=JobForm(data,user=self.employer)
        self.assertNotIn("latitude",form.fields); self.assertNotIn("longitude",form.fields)
        self.assertTrue(form.is_valid(),form.errors)
        job=form.save(commit=False)
        self.assertEqual(job.location,"Santa Maria, CA")
        self.assertIsNotNone(job.latitude); self.assertIsNotNone(job.longitude)

    def test_onsite_job_requires_city_or_zip(self):
        from .forms import JobForm
        data={"company":self.company.pk,"title":"Missing Location","employment_type":Job.EmploymentType.FULL_TIME,"workplace_type":Job.WorkplaceType.ONSITE,"experience_level":Job.ExperienceLevel.ENTRY,"degree_required":Job.DegreeRequired.NONE,"description":"Local work"}
        form=JobForm(data,user=self.employer)
        self.assertFalse(form.is_valid())
        self.assertIn("city or ZIP",str(form.non_field_errors()))

class ExpandedPlatformTests(TestCase):
    def setUp(self):
        self.employer=User.objects.create_user(username="campusrep",email="rep@example.com",personal_email="rep@example.com",password="Pass12345!",role=User.Role.EMPLOYER)
        self.college=Company.objects.create(owner=self.employer,name="Test College",status=Company.Status.APPROVED,is_college=True,college_name="Test College")
        self.job=Job.objects.create(company=self.college,created_by=self.employer,title="Campus Assistant",city="Santa Maria",state="CA",zip_code="93454",location="Santa Maria, CA",employment_type=Job.EmploymentType.PART_TIME,workplace_type=Job.WorkplaceType.ONSITE,experience_level=Job.ExperienceLevel.NONE,degree_required=Job.DegreeRequired.NONE,description="Campus job",status=Job.Status.PUBLISHED,is_on_campus=True,target_school="Test College")
        self.student=User.objects.create_user(username="current",email="personal@example.com",personal_email="personal@example.com",school_email="current@test.edu",student_id="TC123",school_name="Test College",password="Pass12345!",role=User.Role.STUDENT)
        StudentProfile.objects.create(user=self.student)
        self.alumni=User.objects.create_user(username="alumni",email="alumni@example.com",personal_email="alumni@example.com",school_name="Test College",graduation_year=2024,password="Pass12345!",role=User.Role.ALUMNI)
        StudentProfile.objects.create(user=self.alumni)

    def test_registration_requires_student_identifiers(self):
        response=self.client.post(reverse("register"),{"account_type":"student","first_name":"A","last_name":"B","username":"newstudent","personal_email":"new@example.com","school_email":"","student_id":"","school_name":"","password1":"StrongPass123!","password2":"StrongPass123!"})
        self.assertContains(response,"required for current students")

    def test_on_campus_visibility_current_student_only(self):
        self.client.login(username="current",password="Pass12345!")
        self.assertContains(self.client.get(reverse("job_list")),"Campus Assistant")
        self.client.logout(); self.client.login(username="alumni",password="Pass12345!")
        self.assertNotContains(self.client.get(reverse("job_list")),"Campus Assistant")
        self.assertEqual(self.client.get(reverse("job_detail",args=[self.job.pk])).status_code,403)

    def test_staff_student_search_by_id(self):
        staff=User.objects.create_user(username="staff2",email="staff2@example.com",personal_email="staff2@example.com",password="Pass12345!",role=User.Role.STAFF,is_staff=True)
        self.client.login(username="staff2",password="Pass12345!")
        response=self.client.get(reverse("staff_students"),{"q":"TC123"})
        self.assertContains(response,"current")

    def test_resume_exports_and_saves_document(self):
        from .models import ResumeProfile, ResumeExperience
        self.client.login(username="current",password="Pass12345!")
        r=ResumeProfile.objects.create(student=self.student,name="Tech Resume",objective="Obtain a technical internship.",skills="Python, Django")
        ResumeExperience.objects.create(resume=r,title="Student Worker",company="Test College",summary="Helped students.")
        response=self.client.get(reverse("resume_export",args=[r.pk,"pdf"]))
        self.assertEqual(response.status_code,200); self.assertEqual(response["Content-Type"],"application/pdf")
        self.assertTrue(self.student.documents.filter(title__contains="Tech Resume").exists())
