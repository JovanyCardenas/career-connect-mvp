from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        EMPLOYER = "employer", "Employer"
        STAFF = "staff", "Career Center Staff"
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    school_name = models.CharField(max_length=150, blank=True)
    def __str__(self): return self.get_full_name() or self.username


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    headline = models.CharField(max_length=180, blank=True)
    major = models.CharField(max_length=120, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    bio = models.TextField(blank=True)
    skills = models.CharField(max_length=500, blank=True, help_text="Comma-separated skills")
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    open_to_work = models.BooleanField(default=True)
    def completion_percent(self):
        fields = [self.headline, self.major, self.graduation_year, self.bio, self.skills]
        return round(sum(bool(v) for v in fields) / len(fields) * 100)


class StudentDocument(models.Model):
    class Kind(models.TextChoices):
        RESUME = "resume", "Résumé"
        COVER_LETTER = "cover_letter", "Cover letter"
        OTHER = "other", "Other"
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    file = models.FileField(upload_to="student_documents/")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.title} ({self.student})"


class Company(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_companies")
    name = models.CharField(max_length=180)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: verbose_name_plural = "companies"
    def __str__(self): return self.name


class Job(models.Model):
    class EmploymentType(models.TextChoices):
        INTERNSHIP = "internship", "Internship"
        PART_TIME = "part_time", "Part-time"
        FULL_TIME = "full_time", "Full-time"
        CONTRACT = "contract", "Contract"
        TEMPORARY = "temporary", "Temporary"
    class WorkplaceType(models.TextChoices):
        ONSITE = "onsite", "On-site"
        HYBRID = "hybrid", "Hybrid"
        REMOTE = "remote", "Remote"
    class ExperienceLevel(models.TextChoices):
        NONE = "none", "No experience required"
        ENTRY = "entry", "Entry level"
        MID = "mid", "Mid level"
        SENIOR = "senior", "Senior level"
    class DegreeRequired(models.TextChoices):
        NONE = "none", "No degree required"
        HS = "hs", "High school diploma / GED"
        ASSOCIATE = "associate", "AA / AS"
        BACHELOR = "bachelor", "BA / BS"
        MASTER = "master", "MA / MS"
        DOCTORATE = "doctorate", "PhD / Doctorate"
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        PUBLISHED = "published", "Published"
        UNPUBLISHED = "unpublished", "Unpublished"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected"
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_jobs")
    title = models.CharField(max_length=180)
    location = models.CharField(max_length=180)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    workplace_type = models.CharField(max_length=20, choices=WorkplaceType.choices)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    degree_required = models.CharField(max_length=20, choices=DegreeRequired.choices, default=DegreeRequired.NONE)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    skills = models.CharField(max_length=500, blank=True, help_text="Comma-separated skills")
    salary_min = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    salary_max = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_notes = models.TextField(blank=True)
    external_apply_url = models.URLField(blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.title} at {self.company.name}"
    def get_absolute_url(self): return reverse("job_detail", args=[self.pk])
    @property
    def salary_display(self):
        if self.salary_min and self.salary_max: return f"${self.salary_min:,}–${self.salary_max:,}"
        if self.salary_min: return f"From ${self.salary_min:,}"
        return "Salary not listed"


class SavedJob(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["student", "job"], name="unique_saved_job")]


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        NEEDS_CHANGES = "needs_changes", "Changes requested"
        VIEWED = "viewed", "Viewed"
        REVIEW = "review", "Under review"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    cover_letter_text = models.TextField(blank=True)
    resume_document = models.ForeignKey(StudentDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name="resume_applications")
    cover_letter_document = models.ForeignKey(StudentDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name="cover_letter_applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    employer_notes = models.TextField(blank=True)
    staff_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["job", "student"], name="unique_job_application")]
    def __str__(self): return f"{self.student} → {self.job}"
