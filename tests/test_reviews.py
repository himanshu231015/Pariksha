from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution, ReviewDecision, AuditLog

User = get_user_model()
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"

class ReviewWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch_cse = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.sem_5 = Semester.objects.create(program=self.program, number=5, title="Semester 5")
        self.subject_os = Subject.objects.create(branch=self.branch_cse, semester=self.sem_5, code="CS-502", name="Operating Systems")

        self.student = User.objects.create_user(username="student1", password="password123", role=User.ROLE_STUDENT)
        self.reviewer = User.objects.create_user(username="reviewer1", password="password123", role=User.ROLE_REVIEWER, is_staff=True)
        self.admin = User.objects.create_user(username="admin1", password="password123", role=User.ROLE_ADMIN, is_superuser=True)

        self.contrib = PaperContribution.objects.create(
            contributor=self.student,
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            exam_year=2023,
            exam_session="Nov-Dec",
            status=PaperContribution.STATUS_PENDING,
            original_filename="student_scan.pdf",
        )
        self.contrib.file.save("student_scan.pdf", SimpleUploadedFile("student_scan.pdf", VALID_PDF_BYTES))

    def test_anonymous_and_student_denied_from_reviewer_dashboard(self):
        """Students and anonymous visitors cannot access reviewer dashboard."""
        res_anon = self.client.get(reverse("reviews:dashboard"))
        self.assertEqual(res_anon.status_code, 302)

        self.client.login(username="student1", password="password123")
        res_student = self.client.get(reverse("reviews:dashboard"))
        self.assertEqual(res_student.status_code, 403)

    def test_authorized_reviewer_can_approve_contribution(self):
        """Reviewer approval transactionally publishes paper to catalog."""
        self.client.login(username="reviewer1", password="password123")

        post_data = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "decision": ReviewDecision.DECISION_APPROVED,
            "feedback_to_student": "Clean scan, all 8 questions verified.",
            "internal_notes": "Matches RGPV 2023 scheme.",
        }
        res = self.client.post(reverse("reviews:review_detail", args=[self.contrib.id]), post_data)
        self.assertEqual(res.status_code, 302)

        # Contribution updated
        self.contrib.refresh_from_db()
        self.assertEqual(self.contrib.status, PaperContribution.STATUS_APPROVED)

        # Verified AcademicPaper created in catalog
        verified_paper = AcademicPaper.objects.filter(
            subject=self.subject_os,
            exam_year=2023,
            exam_session="Nov-Dec",
            is_verified=True,
        ).first()
        self.assertIsNotNone(verified_paper)
        self.assertEqual(verified_paper.verified_by, self.reviewer)

        # Audit log entry created
        log = AuditLog.objects.filter(action="PAPER_APPROVED_AND_PUBLISHED").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.reviewer)

    def test_authorized_reviewer_rejection_requires_reason(self):
        """Reviewer rejection requires an explanation note for the student."""
        self.client.login(username="reviewer1", password="password123")

        # Missing feedback should fail validation
        post_data_empty_feedback = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "decision": ReviewDecision.DECISION_REJECTED,
            "feedback_to_student": "",  # Empty!
        }
        res = self.client.post(reverse("reviews:review_detail", args=[self.contrib.id]), post_data_empty_feedback)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Please provide a clear reason")

        # With feedback
        post_data_with_feedback = {
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.sem_5.id,
            "subject": self.subject_os.id,
            "exam_year": 2023,
            "exam_session": "Nov-Dec",
            "decision": ReviewDecision.DECISION_REJECTED,
            "feedback_to_student": "Pages 2 and 3 are illegible and cropped.",
        }
        res_ok = self.client.post(reverse("reviews:review_detail", args=[self.contrib.id]), post_data_with_feedback)
        self.assertEqual(res_ok.status_code, 302)
        self.contrib.refresh_from_db()
        self.assertEqual(self.contrib.status, PaperContribution.STATUS_REJECTED)

    def test_contributor_cannot_review_own_submission(self):
        """Security: A student contributor cannot review or approve their own paper."""
        # Elevate student to reviewer role
        self.student.role = User.ROLE_REVIEWER
        self.student.save()

        self.client.login(username="student1", password="password123")
        res = self.client.get(reverse("reviews:review_detail", args=[self.contrib.id]))
        # Should redirect with security warning
        self.assertEqual(res.status_code, 302)

    def test_reviewers_cannot_access_admin_console(self):
        """Standard reviewers are denied from administrator-only console."""
        self.client.login(username="reviewer1", password="password123")
        res = self.client.get(reverse("reviews:admin_dashboard"))
        self.assertEqual(res.status_code, 403)
