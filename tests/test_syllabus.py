from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.syllabus.models import SyllabusDocument

User = get_user_model()
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"

class SyllabusManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch_cse = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.sem_5 = Semester.objects.create(program=self.program, number=5, title="Semester 5")
        self.subject_os = Subject.objects.create(branch=self.branch_cse, semester=self.sem_5, code="CS-502", name="Operating Systems")

        self.student = User.objects.create_user(username="student1", password="password123", role=User.ROLE_STUDENT)
        self.admin = User.objects.create_user(username="admin1", password="password123", role=User.ROLE_ADMIN, is_superuser=True)

        # Published syllabus
        self.pub_syllabus = SyllabusDocument.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            academic_year="2023-2024",
            version="1.0",
            title="CS-502 Published Syllabus",
            is_published=True,
            uploaded_by=self.admin,
        )
        self.pub_syllabus.file.save("pub.pdf", SimpleUploadedFile("pub.pdf", VALID_PDF_BYTES))

        # Draft syllabus
        self.draft_syllabus = SyllabusDocument.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            academic_year="2024-2025",
            version="2.0-draft",
            title="CS-502 Draft Syllabus",
            is_published=False,
            uploaded_by=self.admin,
        )
        self.draft_syllabus.file.save("draft.pdf", SimpleUploadedFile("draft.pdf", VALID_PDF_BYTES))

    def test_student_cannot_access_syllabus_upload(self):
        """Students cannot upload syllabus documents (403 Forbidden)."""
        self.client.login(username="student1", password="password123")
        res = self.client.get(reverse("syllabus:upload"))
        self.assertEqual(res.status_code, 403)

    def test_admin_can_upload_syllabus(self):
        """Admin can upload an official syllabus PDF."""
        self.client.login(username="admin1", password="password123")
        upload_pdf = SimpleUploadedFile("scheme.pdf", VALID_PDF_BYTES, content_type="application/pdf")
        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "academic_year": "2024-2025",
            "version": "v3.0",
            "title": "Official 2024 Scheme - CS502",
            "is_published": True,
            "file": upload_pdf,
        }
        res = self.client.post(reverse("syllabus:upload"), post_data)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(SyllabusDocument.objects.filter(version="v3.0").exists())

    def test_unpublished_syllabus_hidden_from_students(self):
        """Students see only published syllabus documents."""
        self.client.login(username="student1", password="password123")
        res = self.client.get(reverse("syllabus:list"))
        self.assertContains(res, "CS-502 Published Syllabus")
        self.assertNotContains(res, "CS-502 Draft Syllabus")

        # Attempt to download draft syllabus
        dl_res = self.client.get(reverse("syllabus:download", args=[self.draft_syllabus.id]))
        self.assertEqual(dl_res.status_code, 403)

    def test_admin_can_toggle_publish(self):
        """Administrator can toggle publish/unpublish status."""
        self.client.login(username="admin1", password="password123")
        res = self.client.get(reverse("syllabus:toggle_publish", args=[self.draft_syllabus.id]))
        self.assertEqual(res.status_code, 302)
        self.draft_syllabus.refresh_from_db()
        self.assertTrue(self.draft_syllabus.is_published)
