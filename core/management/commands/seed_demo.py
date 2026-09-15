from datetime import date, timedelta
from django.core.management.base import BaseCommand
from core.models import Application, Company, Job, StudentProfile, User

class Command(BaseCommand):
    help = "Create demonstration accounts and data"

    def handle(self, *args, **kwargs):
        staff, _ = User.objects.get_or_create(username="staff", defaults={"email":"staff@example.com", "personal_email":"staff@example.com", "first_name":"Career", "last_name":"Staff", "role":User.Role.STAFF, "is_staff":True})
        staff.personal_email=staff.personal_email or "staff@example.com"; staff.email=staff.personal_email; staff.set_password("DemoPass123!"); staff.save()
        employer, _ = User.objects.get_or_create(username="employer", defaults={"email":"employer@example.com", "personal_email":"employer@example.com", "first_name":"Taylor", "last_name":"Recruiter", "role":User.Role.EMPLOYER})
        employer.personal_email=employer.personal_email or "employer@example.com"; employer.email=employer.personal_email; employer.set_password("DemoPass123!"); employer.save()
        student, _ = User.objects.get_or_create(username="student", defaults={"email":"student@example.com", "personal_email":"student@example.com", "school_email":"jstudent@demo.edu", "student_id":"DSU10001", "first_name":"Jordan", "last_name":"Student", "role":User.Role.STUDENT, "school_name":"Demo State University"})
        student.personal_email=student.personal_email or "student@example.com"; student.email=student.personal_email; student.school_email=student.school_email or "jstudent@demo.edu"; student.student_id=student.student_id or "DSU10001"; student.school_name=student.school_name or "Demo State University"; student.set_password("DemoPass123!"); student.save()
        profile, _ = StudentProfile.objects.get_or_create(user=student)
        profile.headline = "Software engineering student seeking internships"
        profile.major = "Software Engineering"
        profile.graduation_year = 2027
        profile.bio = "Student developer with experience building Django applications and technical projects."
        profile.skills = "Python, Django, JavaScript, SQL, Git"
        profile.save()
        company, _ = Company.objects.get_or_create(owner=employer, name="Northstar Technology", defaults={"website":"https://example.com", "industry":"Technology", "location":"San Jose, CA", "description":"A growing technology company building software for education and business.", "status":Company.Status.APPROVED})
        company.status = Company.Status.APPROVED; company.save()
        jobs = [
            ("Software Engineering Intern", "San Jose, CA", Job.EmploymentType.INTERNSHIP, Job.WorkplaceType.HYBRID, 24, 32),
            ("Junior Web Developer", "Remote", Job.EmploymentType.FULL_TIME, Job.WorkplaceType.REMOTE, 65000, 82000),
            ("IT Support Student Assistant", "San Jose, CA", Job.EmploymentType.PART_TIME, Job.WorkplaceType.ONSITE, 22, 27),
        ]
        for title, location, etype, wtype, smin, smax in jobs:
            Job.objects.get_or_create(company=company, title=title, defaults={
                "created_by": employer, "location":location, "employment_type":etype, "workplace_type":wtype,
                "description":f"Join {company.name} as a {title}. Work on practical projects, collaborate with a supportive team, and develop professional experience.",
                "requirements":"Strong communication skills, willingness to learn, and relevant coursework or project experience.",
                "skills":"Python, JavaScript, Communication, Problem Solving", "salary_min":smin, "salary_max":smax,
                "status":Job.Status.PUBLISHED, "application_deadline":date.today()+timedelta(days=45)
            })

        college, _ = Company.objects.get_or_create(owner=employer, name="Demo State University", defaults={"industry":"Higher Education","location":"Santa Maria, CA","description":"Campus employment office.","status":Company.Status.APPROVED,"is_college":True,"college_name":"Demo State University"})
        college.status=Company.Status.APPROVED; college.is_college=True; college.college_name="Demo State University"; college.save()
        Job.objects.get_or_create(company=college,title="Campus Technology Assistant",defaults={"created_by":employer,"location":"Santa Maria, CA","city":"Santa Maria","state":"CA","zip_code":"93454","latitude":34.953,"longitude":-120.4357,"employment_type":Job.EmploymentType.PART_TIME,"workplace_type":Job.WorkplaceType.ONSITE,"description":"Support campus computer labs and classroom technology.","requirements":"Must be a currently enrolled Demo State University student.","skills":"Customer service, IT support","salary_min":18,"salary_max":22,"status":Job.Status.PUBLISHED,"is_on_campus":True,"target_school":"Demo State University"})
        self.stdout.write(self.style.SUCCESS("Demo data created. Password for all demo users: DemoPass123!"))
