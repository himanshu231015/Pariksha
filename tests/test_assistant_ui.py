from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.assistant_ui.services import AssistantService
from apps.assistant_ui.schemas import AssistantInquiryRequest

User = get_user_model()

class AssistantUIBoundaryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test_student", password="password123")
        self.client.login(username="test_student", password="password123")

    def test_assistant_chat_page_loads(self):
        """Ask Pariksha chat interface loads cleanly."""
        res = self.client.get(reverse("assistant_ui:chat"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Ask Pariksha")
        self.assertContains(res, "Awaiting Model Integration")

    def test_chat_submission_returns_honest_pending_notice(self):
        """Submitting an inquiry returns an honest integration-pending contract state."""
        post_data = {
            "message": "Explain CPU Scheduling algorithms for 7 marks",
            "requested_format": "detailed",
            "workflow_intent": "exam_prep",
        }
        res = self.client.post(reverse("assistant_ui:chat"), post_data)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AI Backend Not Connected")
        self.assertContains(res, "pending_integration")
        self.assertContains(res, "Explain CPU Scheduling algorithms for 7 marks")

    def test_service_boundary_unconfigured_contract(self):
        """Service boundary strictly reports unconfigured state without fake model."""
        self.assertFalse(AssistantService.is_ai_backend_configured())
        inquiry = AssistantInquiryRequest(message="Test query")
        response = AssistantService.send_inquiry(inquiry)
        self.assertEqual(response.status_code if hasattr(response, 'status_code') else response.status, "pending_integration")
        self.assertIn("AI Backend Not Connected", response.answer_text)
        self.assertEqual(len(response.sources), 0)

    def test_must_prepare_interface_loads(self):
        """Must Prepare page renders with honest analysis pending message."""
        res = self.client.get(reverse("assistant_ui:must_prepare"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Must Prepare Topics")
        self.assertContains(res, "Analysis Engine Pending")

    def test_predicted_paper_interface_loads(self):
        """Predicted paper page renders disclaimer and configuration fields."""
        res = self.client.get(reverse("assistant_ui:predicted_paper"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Predicted Practice Paper")
        self.assertContains(res, "This is NOT an actual or leaked university examination paper")
