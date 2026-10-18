import io
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution

User = get_user_model()

VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"

def generate_test_image():
    file_obj = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="blue")
    image.save(file_obj, format="PNG")
    file_obj.seek(0)
    return file_obj.read()

class PaperContributionWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch_cse = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.sem_5 = Semester.objects.create(program=self.program, number=5, title="Semester 5")
        self.subject_os = Subject.objects.create(branch=self.branch_cse, semester=self.sem_5, code="CS-502", name="Operating Systems")

        self.student = User.objects.create_user(username="student1", password="password123", role=User.ROLE_STUDENT)
        self.client.login(username="student1", password="password123")

    def test_valid_pdf_contribution(self):
        """Student can submit a valid PDF question paper."""
        uploaded_file = SimpleUploadedFile("os_2023.pdf", VALID_PDF_BYTES, content_type="application/pdf")
        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "notes": "Scanned from original exam hall copy",
            "file": uploaded_file,
        }
        response = self.client.post(reverse("reviews:contribute"), post_data)
        self.assertEqual(response.status_code, 302)

        contrib = PaperContribution.objects.filter(contributor=self.student).first()
        self.assertIsNotNone(contrib)
        self.assertEqual(contrib.status, PaperContribution.STATUS_PENDING)
        self.assertEqual(contrib.exam_year, 2023)
        self.assertEqual(contrib.exam_session, "Nov-Dec")
        self.assertEqual(contrib.original_filename, "os_2023.pdf")

    def test_valid_image_contribution(self):
        """Student can submit a valid PNG scan."""
        img_bytes = generate_test_image()
        uploaded_img = SimpleUploadedFile("scan.png", img_bytes, content_type="image/png")
        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "May-June",
            "file": uploaded_img,
        }
        response = self.client.post(reverse("reviews:contribute"), post_data)
        self.assertEqual(response.status_code, 302)
        contrib = PaperContribution.objects.filter(exam_session="May-June").first()
        self.assertIsNotNone(contrib)

    def test_unsupported_file_extension_rejected(self):
        """Unsupported extensions (e.g. .exe or .txt) must be rejected."""
        bad_file = SimpleUploadedFile("malicious.exe", b"executable_data", content_type="application/x-msdownload")
        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "file": bad_file,
        }
        response = self.client.post(reverse("reviews:contribute"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported file type")
        self.assertEqual(PaperContribution.objects.count(), 0)

    def test_duplicate_paper_prevention_when_approved_paper_exists(self):
        """Submission must be rejected if an approved paper for identical context exists."""
        AcademicPaper.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            exam_year=2023,
            exam_session="Nov-Dec",
            is_verified=True,
        )

        uploaded_file = SimpleUploadedFile("duplicate.pdf", VALID_PDF_BYTES, content_type="application/pdf")
        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "file": uploaded_file,
        }
        response = self.client.post(reverse("reviews:contribute"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already available in the Pariksha catalog")
        self.assertEqual(PaperContribution.objects.count(), 0)

    def test_student_cannot_access_other_students_private_files(self):
        """Students cannot download private scans belonging to other students."""
        other_student = User.objects.create_user(username="other_student", password="pwd", role=User.ROLE_STUDENT)
        other_contrib = PaperContribution.objects.create(
            contributor=other_student,
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            exam_year=2021,
            exam_session="Nov-Dec",
            status=PaperContribution.STATUS_PENDING,
        )
        other_contrib.file.save("private.pdf", SimpleUploadedFile("private.pdf", VALID_PDF_BYTES))

        # Logged in as student1, attempting to access other_student's contribution file
        res = self.client.get(reverse("reviews:contribution_file", args=[other_contrib.id]))
        self.assertEqual(res.status_code, 403)
