from datetime import date, timedelta
from django.core.management.base import BaseCommand
from core.models import Application, Company, Job, StudentProfile, User

class Command(BaseCommand):
    help = "Create demonstration accounts and data"

    def handle(self, *args, **kwargs):
        staff, _ = User.objects.get_or_create(username="staff", defaults={"email":"staff@example.com", "first_name":"Career", "last_name":"Staff", "role":User.Role.STAFF, "is_staff":True})
        staff.set_password("DemoPass123!"); staff.save()
        employer, _ = User.objects.get_or_create(username="employer", defaults={"email":"employer@example.com", "first_name":"Taylor", "last_name":"Recruiter", "role":User.Role.EMPLOYER})
        employer.set_password("DemoPass123!"); employer.save()
        student, _ = User.objects.get_or_create(username="student", defaults={"email":"student@example.com", "first_name":"Jordan", "last_name":"Student", "role":User.Role.STUDENT, "school_name":"Demo State University"})
        student.set_password("DemoPass123!"); student.save()
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
        self.stdout.write(self.style.SUCCESS("Demo data created. Password for all demo users: DemoPass123!"))
