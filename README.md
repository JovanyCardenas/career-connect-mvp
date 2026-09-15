# CareerConnect MVP

CareerConnect is a development-stage college job platform inspired by the core workflows found in Handshake, Indeed, JobSpeaker, and LinkedIn. It is an original Django implementation, not copied source code or branding.

## Included now

- Student, employer, and career-center staff roles
- Registration, login, logout, and role-based dashboards
- Student career profiles and résumé upload
- Company creation and staff approval
- Job creation and staff publishing workflow
- Search and filters for published jobs
- Saved jobs
- Internal job applications
- Employer applicant review and status updates
- Django admin
- Demo accounts and sample jobs
- Automated smoke tests
- Docker setup

## Fast local setup

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open: http://127.0.0.1:8000

## Demo accounts

All use password `DemoPass123!`:

- Student: `student`
- Employer: `employer`
- Career staff: `staff`

The staff user can also open `/admin/` because the seed command marks it as Django staff. It is not a superuser; create one when needed:

```bash
python manage.py createsuperuser
```

## Docker

```bash
docker compose up --build
```

Then open http://127.0.0.1:8000.

## Run tests

```bash
python manage.py test
```

## Important development limitations

This package is a functional MVP for local testing, not a production-complete replacement for a mature commercial platform. Before public launch, add PostgreSQL, email verification, password reset email delivery, object-level audit logs, malware scanning for uploads, cloud file storage, rate limiting, stronger employer verification, accessibility testing, privacy/terms documents, backups, observability, deployment secrets, and a tenant architecture if multiple schools will use one installation.

## Suggested next build order

1. PostgreSQL and tenant/school memberships
2. Email verification and invitation flows
3. Employer team members and granular permissions
4. Application status history and notifications
5. Events, career fairs, and appointments
6. Reporting and placement outcomes
7. REST API and optional mobile/React client

## Expanded management features

This replacement build adds:

- Multiple approved companies per employer account, with explicit company selection on each job
- Editing of published/rejected jobs with automatic return to pending staff review
- Employer applicant detail pages with student profile, resume, cover letter and application content
- Student Document Hub with reusable resumes, cover letters and deletion controls
- Staff directories for students and employers, account editing, and password-reset email actions
- Staff company, job and application management, including publish, unpublish, reject, edit and changes-requested workflows
- Job filters for experience level, degree requirement, minimum salary and radius around supported city centers
- Employer-friendly address, city, state, and ZIP fields with automatic geocoding for radius filtering

### Radius search notes

Employers and staff never enter latitude or longitude. For on-site and hybrid postings, the form requires at least a city or ZIP code and automatically geocodes the best available location. It tries the complete street address first, then city/state, then ZIP. Remote jobs can omit physical location information and remain included in radius searches.

The development build uses OpenStreetMap Nominatim for low-volume testing and includes offline fallback coordinates for Santa Maria, San Luis Obispo, San Jose, and several demo ZIP codes. Before production, configure a dedicated commercial or self-hosted geocoding provider and follow its usage policy.

### Development email

Password reset emails use Django's console email backend. During local testing, the reset link is printed in the server terminal. Configure a real transactional email provider before deployment.


## Geocoding configuration

Optional Django settings:

```python
GEOCODING_URL = "https://nominatim.openstreetmap.org/search"
GEOCODING_USER_AGENT = "CareerConnect-Development/1.0"
GEOCODING_TIMEOUT = 4
```

Production systems should use a provider intended for application traffic, cache results, and avoid geocoding an unchanged address repeatedly.

## Expanded account and career-center features

- Account selection for current students, employers, alumni, and community guests.
- Current students store a student ID, personal email, school email, and school name.
- Alumni can store their former ID/school email and must enter graduation year.
- College companies can publish school-restricted on-campus jobs. These appear first only for matching current students and are hidden from all other audiences.
- Staff list pages include search by name, username, student ID, email, company, job, and related records.
- Staff announcements support text, images, optional links, school-specific audiences, scheduling, and hidden/inactive states.
- Students and alumni can create multiple targeted resume profiles with objectives, skills, experience, education, projects, awards, and certificates.
- Resume sections with no content are omitted from preview and exports.
- PDF and DOCX exports download immediately and are also saved in the student's Document Hub.

For production resume generation, install LibreOffice if you want server-side DOCX-to-PDF parity checks. The included app generates PDFs directly using ReportLab and DOCX files using python-docx.
