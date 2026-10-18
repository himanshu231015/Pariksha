from django.test import TestCase, Client
from django.urls import reverse
from apps.academics.models import University, Program, Branch, Semester, Subject

class GeneralApplicationRoutesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.sem = Semester.objects.create(program=self.program, number=1, title="Sem 1")
        self.subject = Subject.objects.create(branch=self.branch, semester=self.sem, code="CS-101", name="Intro to Computing")

    def test_landing_page(self):
        """Home page loads with 200 OK and brand name Pariksha."""
        res = self.client.get(reverse("core:home"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Pariksha")
        self.assertContains(res, "RGPV")

    def test_health_check_endpoint(self):
        """Health check returns 200 JSON status."""
        res = self.client.get(reverse("core:health"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "Pariksha")

    def test_legal_and_informational_pages(self):
        """Privacy, terms, disclaimer, and contact pages load cleanly."""
        for route in ["core:privacy", "core:terms", "core:disclaimer", "core:contact"]:
            res = self.client.get(reverse(route))
            self.assertEqual(res.status_code, 200)

    def test_cascading_academic_api(self):
        """API endpoints return JSON choices for frontend dropdowns."""
        res_branches = self.client.get(reverse("academics:api_branches"), {"program_id": self.program.id})
        self.assertEqual(res_branches.status_code, 200)
        self.assertEqual(len(res_branches.json()["branches"]), 1)

        res_subjects = self.client.get(reverse("academics:api_subjects"), {"branch_id": self.branch.id})
        self.assertEqual(res_subjects.status_code, 200)
        self.assertEqual(len(res_subjects.json()["subjects"]), 1)
        self.assertEqual(res_subjects.json()["subjects"][0]["code"], "CS-101")
