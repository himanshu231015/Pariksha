import os
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.papers.models import AcademicPaper

User = get_user_model()

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"
SAMPLE_SOLUTION_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>\n% PYQ OFFICIAL SOLUTION\nendobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"

class PYQSolutionFeatureTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch = Branch.objects.create(program=self.program, name="Computer Science", code="CSE")
        self.semester = Semester.objects.create(program=self.program, number=5, title="Semester 5")
        self.subject = Subject.objects.create(branch=self.branch, semester=self.semester, code="CS-501", name="Data Communication")

        self.student = User.objects.create_user(username="student_user", password="password123", role=User.ROLE_STUDENT)
        self.admin = User.objects.create_superuser(username="admin_user", password="password123", email="admin@pariksha.org")

        self.paper = AcademicPaper.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch,
            semester=self.semester,
            subject=self.subject,
            exam_year=2023,
            exam_session="Nov-Dec",
            paper_title="CS-501 Data Communication Nov-Dec 2023",
            is_verified=True,
        )
        self.paper.file.save("cs501_2023.pdf", ContentFile(SAMPLE_PDF_BYTES))

    def test_detail_page_shows_coming_soon_when_no_solution_uploaded(self):
        """When admin has not uploaded a solution, detail page shows Coming Soon."""
        self.client.login(username="student_user", password="password123")
        response = self.client.get(reverse("papers:detail", args=[self.paper.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coming Soon")
        self.assertContains(response, "Admin has not uploaded the solution yet")
        self.assertFalse(self.paper.has_solution)

    def test_download_and_preview_return_404_when_solution_not_uploaded(self):
        """Accessing solution download or preview when no solution exists returns 404."""
        self.client.login(username="student_user", password="password123")
        res_dl = self.client.get(reverse("papers:solution_download", args=[self.paper.id]))
        self.assertEqual(res_dl.status_code, 404)

        res_prev = self.client.get(reverse("papers:solution_preview", args=[self.paper.id]))
        self.assertEqual(res_prev.status_code, 404)

    def test_admin_can_upload_solution(self):
        """Admin can upload a solution file which is then accessible."""
        self.client.login(username="admin_user", password="password123")
        upload_file = SimpleUploadedFile("cs501_solution.pdf", SAMPLE_SOLUTION_BYTES, content_type="application/pdf")
        
        response = self.client.post(
            reverse("papers:upload_solution", args=[self.paper.id]),
            {"solution_file": upload_file},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.paper.refresh_from_db()
        self.assertTrue(self.paper.has_solution)
        self.assertIsNotNone(self.paper.solution_uploaded_at)
        self.assertEqual(self.paper.solution_uploaded_by, self.admin)

        # Now detail page shows Solution Available
        res_detail = self.client.get(reverse("papers:detail", args=[self.paper.id]))
        self.assertContains(res_detail, "Solution Available")
        self.assertContains(res_detail, "Download Solution PDF")

    def test_student_cannot_upload_solution(self):
        """Normal student gets 403 Forbidden when trying to upload solution."""
        self.client.login(username="student_user", password="password123")
        upload_file = SimpleUploadedFile("hack_sol.pdf", SAMPLE_SOLUTION_BYTES, content_type="application/pdf")
        response = self.client.post(
            reverse("papers:upload_solution", args=[self.paper.id]),
            {"solution_file": upload_file},
        )
        self.assertEqual(response.status_code, 403)
        self.paper.refresh_from_db()
        self.assertFalse(self.paper.has_solution)

    def test_student_can_preview_and_download_uploaded_solution(self):
        """Once solution is uploaded, students can preview and download it with incremented stats."""
        self.paper.solution_file.save("cs501_sol_verified.pdf", ContentFile(SAMPLE_SOLUTION_BYTES))
        self.paper.solution_uploaded_by = self.admin
        self.paper.save()

        self.client.login(username="student_user", password="password123")

        # Preview
        res_prev = self.client.get(reverse("papers:solution_preview", args=[self.paper.id]))
        self.assertEqual(res_prev.status_code, 200)
        self.assertEqual(res_prev["Content-Type"], "application/pdf")
        self.assertIn("inline", res_prev["Content-Disposition"])

        # Download
        res_dl = self.client.get(reverse("papers:solution_download", args=[self.paper.id]))
        self.assertEqual(res_dl.status_code, 200)
        self.assertIn("attachment", res_dl["Content-Disposition"])
        self.assertIn("CS-501_Nov-Dec_2023_Solution.pdf", res_dl["Content-Disposition"])

        # Verify download count incremented
        self.paper.refresh_from_db()
        self.assertEqual(self.paper.solution_downloads_count, 1)

    def test_admin_can_delete_solution_and_reverts_to_coming_soon(self):
        """Admin can remove a solution to revert back to Coming Soon status."""
        self.paper.solution_file.save("cs501_temp.pdf", ContentFile(SAMPLE_SOLUTION_BYTES))
        self.paper.save()
        self.assertTrue(self.paper.has_solution)

        self.client.login(username="admin_user", password="password123")
        res = self.client.post(reverse("papers:delete_solution", args=[self.paper.id]), follow=True)
        self.assertEqual(res.status_code, 200)

        self.paper.refresh_from_db()
        self.assertFalse(self.paper.has_solution)
        self.assertContains(res, "Coming Soon")
