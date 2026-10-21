import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject, SyllabusUnit
from apps.papers.models import AcademicPaper
from apps.assistant_ui.services import AssistantService
from apps.assistant_ui.schemas import AssistantInquiryRequest

User = get_user_model()


class AssistantUIBoundaryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test_student", password="password123")
        self.client.login(username="test_student", password="password123")

        # Set up sample academic hierarchy
        self.uni = University.objects.create(name="Rajiv Gandhi Proudyogiki Vishwavidyalaya", short_name="RGPV Bhopal", code="RGPV")
        self.prog = Program.objects.create(university=self.uni, name="Bachelor of Technology", code="B.Tech")
        self.branch = Branch.objects.create(program=self.prog, name="CSE - Artificial Intelligence", code="AL")
        self.semester = Semester.objects.create(program=self.prog, number=7, title="Semester VII (7th Sem)")
        self.subject = Subject.objects.create(branch=self.branch, semester=self.semester, code="AL-503(b)", name="Data Visualization and Analytics")
        self.unit = SyllabusUnit.objects.create(
            subject=self.subject, unit_number=1, title="Unit 1: Fundamentals of Data Visualization", description="Visualization pipeline, visual perception"
        )

    def test_assistant_chat_page_loads(self):
        """Ask Pariksha chat interface loads cleanly with Academic Context and Apply button."""
        res = self.client.get(reverse("assistant_ui:chat"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Ask Pariksha")
        self.assertContains(res, "Academic Context")
        self.assertContains(res, "Apply Academic Context")

    def test_apply_context_api(self):
        """Applying academic context saves state and returns tailored questions."""
        payload = {
            "university": self.uni.id,
            "program": self.prog.id,
            "branch": self.branch.id,
            "semester": self.semester.id,
            "subject": self.subject.id,
            "workflow_intent": "exam_prep",
            "requested_format": "detailed",
        }
        res = self.client.post(
            reverse("assistant_ui:api_apply_context"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["context"]["subject_code"], "AL-503(b)")
        self.assertTrue(len(data["suggested_questions"]) > 0)
        self.assertIn("Pipeline", data["suggested_questions"][0])

    def test_ask_question_api_pyq_search_and_tool_fallback(self):
        """Question triggers search in PYQ solutions first, then Academic Tool Call."""
        payload = {
            "message": "Explain Data Visualization Pipeline with schematic diagram for 7 marks",
            "subject": self.subject.id,
            "workflow_intent": "exam_prep",
            "requested_format": "detailed",
        }
        res = self.client.post(
            reverse("assistant_ui:api_ask_question"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("response", data)
        self.assertIn("Pipeline", data["response"]["answer_text"])
        # Should be either found in PYQ or synthesized via academic tool call
        self.assertIn(data["response"]["status"], ["found_in_pyq", "tool_synthesized_academic", "tool_synthesized_gemini"])

    def test_service_answering_pipeline(self):
        """Service boundary searches PYQ solutions and falls back to academic tool engine."""
        inquiry = AssistantInquiryRequest(
            message="Explain Data Visualization Pipeline with diagram",
            subject_id=self.subject.id,
            requested_format="detailed",
        )
        response = AssistantService.send_inquiry(inquiry)
        self.assertIn(response.status, ["found_in_pyq", "tool_synthesized_academic", "tool_synthesized_gemini"])
        self.assertTrue(len(response.answer_text) > 50)
        self.assertIn("Pipeline", response.answer_text)

    def test_must_prepare_interface_loads(self):
        """Must Prepare page renders."""
        res = self.client.get(reverse("assistant_ui:must_prepare"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Must Prepare Topics")

    def test_predicted_paper_interface_loads(self):
        """Predicted paper page renders disclaimer and configuration fields."""
        res = self.client.get(reverse("assistant_ui:predicted_paper"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Predicted Practice Paper")
