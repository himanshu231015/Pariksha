"""
Integration Service Boundary for Future AI/LLM Functionality.

Pariksha strictly separates the web application & database layer from future AI
models and inference pipelines.
"""
import logging
from django.conf import settings
from .schemas import (
    AssistantInquiryRequest,
    AssistantInquiryResponse,
    SourceCitation,
    MustPrepareTopicItem,
    PredictedPaperResponse,
)

logger = logging.getLogger("pariksha")

class AssistantService:
    """Service handling future API communication with the AI inference layer."""

    @classmethod
    def is_ai_backend_configured(cls) -> bool:
        """Check whether future AI backend service URL and credentials are set."""
        service_url = getattr(settings, "FUTURE_AI_SERVICE_URL", "")
        api_key = getattr(settings, "FUTURE_AI_SERVICE_API_KEY", "")
        # For non-AI phase: strictly return False unless real endpoint is provided
        return bool(service_url and api_key)

    @classmethod
    def send_inquiry(cls, inquiry: AssistantInquiryRequest) -> AssistantInquiryResponse:
        """
        Send student academic inquiry to the AI backend.
        
        Currently returns an honest pending integration contract state without
        substituting canned responses for real model output.
        """
        if not cls.is_ai_backend_configured():
            return AssistantInquiryResponse(
                status="pending_integration",
                answer_text=(
                    "AI Backend Not Connected: The Ask Pariksha AI inference and RAG pipeline "
                    "is scheduled for integration in the next project phase. "
                    "No AI model or foundation service is currently connected to process your query."
                ),
                sources=[],
                model_version=None,
                index_version=None,
                limitations_disclaimer=(
                    "This interface contract is established and ready. "
                    "Once the model service is deployed, answers will be grounded directly "
                    "in verified RGPV syllabus documents and verified PYQ papers."
                ),
            )

        # Future integration: call external microservice via http_client
        logger.info(f"Future AI service dispatch requested for topic: {inquiry.message[:50]}...")
        return AssistantInquiryResponse(
            status="pending_integration",
            answer_text="External AI service connection is in progress.",
        )

    @classmethod
    def get_must_prepare_topics(cls, subject_id: int):
        """
        Fetch topic prioritization.
        Returns empty list when no real statistical/AI topic analysis is available.
        """
        # Strictly return empty list rather than inventing fictitious priority rankings
        return []

    @classmethod
    def generate_predicted_paper(cls, subject_id: int, total_marks: int, duration_minutes: int):
        """
        Generate predicted practice paper.
        Returns None to indicate AI model has not generated this paper.
        """
        return None
