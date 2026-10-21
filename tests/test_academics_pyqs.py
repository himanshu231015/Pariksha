from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution

User = get_user_model()

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"

class AcademicsAndPYQSearchTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch_cse = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.branch_it = Branch.objects.create(program=self.program, name="IT", code="IT")
        self.sem_5 = Semester.objects.create(program=self.program, number=5, title="Semester 5")
        self.sem_6 = Semester.objects.create(program=self.program, number=6, title="Semester 6")

        self.subject_os = Subject.objects.create(branch=self.branch_cse, semester=self.sem_5, code="CS-502", name="Operating Systems")
        self.subject_dbms = Subject.objects.create(branch=self.branch_cse, semester=self.sem_5, code="CS-503", name="Database Management")

        self.student = User.objects.create_user(username="student1", password="password123", role=User.ROLE_STUDENT)
        self.client.login(username="student1", password="password123")

        # Approved paper 1 (CS-502, 2023, Nov-Dec)
        self.paper1 = AcademicPaper.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_os,
            exam_year=2023,
            exam_session="Nov-Dec",
            paper_title="CS-502 Operating Systems Nov-Dec 2023",
            is_verified=True,
        )
        self.paper1.file.save("test_os_2023.pdf", ContentFile(SAMPLE_PDF_BYTES))

        # Approved paper 2 (CS-503, 2022, May-June)
        self.paper2 = AcademicPaper.objects.create(
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_5,
            subject=self.subject_dbms,
            exam_year=2022,
            exam_session="May-June",
            paper_title="CS-503 DBMS May-June 2022",
            is_verified=True,
        )
        self.paper2.file.save("test_dbms_2022.pdf", ContentFile(SAMPLE_PDF_BYTES))

    def test_pyq_list_renders_verified_papers(self):
        """PYQ list page shows verified papers."""
        response = self.client.get(reverse("papers:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS-502")
        self.assertContains(response, "Operating Systems")
        self.assertContains(response, "CS-503")
        self.assertContains(response, "Database Management")

    def test_pyq_filtering_by_subject_and_year(self):
        """Filtering by subject or year returns precise subsets."""
        response = self.client.get(reverse("papers:list"), {"subject": self.subject_os.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["papers"]), 1)
        self.assertEqual(response.context["papers"][0]["latest_paper"].id, self.paper1.id)

        # Filter by year 2022
        response_year = self.client.get(reverse("papers:list"), {"year": 2022})
        self.assertEqual(response_year.status_code, 200)
        self.assertEqual(len(response_year.context["papers"]), 1)
        self.assertEqual(response_year.context["papers"][0]["latest_paper"].id, self.paper2.id)
        self.assertEqual(response_year.context["papers"][0]["subject"].code, "CS-503")

    def test_unapproved_contributions_not_shown_in_search(self):
        """Pending student contributions must never appear in public search."""
        PaperContribution.objects.create(
            contributor=self.student,
            university=self.university,
            program=self.program,
            branch=self.branch_cse,
            semester=self.sem_6,
            subject=self.subject_os,
            exam_year=2024,
            exam_session="May-June",
            status=PaperContribution.STATUS_PENDING,
            original_filename="secret_scan.pdf",
        )
        response = self.client.get(reverse("papers:list"))
        self.assertNotContains(response, "secret_scan.pdf")
        self.assertNotContains(response, "2024")

    def test_paper_download_authorization(self):
        """Download requires authentication and delivers FileResponse."""
        # Unauthenticated user redirected to login
        self.client.logout()
        res_anon = self.client.get(reverse("papers:download", args=[self.paper1.id]))
        self.assertEqual(res_anon.status_code, 302)

        # Authenticated student can download
        self.client.login(username="student1", password="password123")
        res_auth = self.client.get(reverse("papers:download", args=[self.paper1.id]))
        self.assertEqual(res_auth.status_code, 200)
        self.assertEqual(res_auth["Content-Type"], "application/pdf")

        # Verify downloads count incremented
        self.paper1.refresh_from_db()
        self.assertEqual(self.paper1.downloads_count, 1)

    def test_unknown_paper_id_returns_404(self):
        """Non-existent paper ID safely returns 404."""
        self.client.login(username="student1", password="password123")
        response = self.client.get(reverse("papers:detail", args=[999999]))
        self.assertEqual(response.status_code, 404)
        download_res = self.client.get(reverse("papers:download", args=[999999]))
        self.assertEqual(download_res.status_code, 404)
