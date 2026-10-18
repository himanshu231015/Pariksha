"""
Future AI Integration Schemas & Interface Contracts.

These data structures define the exact contract between Pariksha's frontend/Django backend
and the future standalone AI inference/RAG microservice.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class SourceCitation:
    """Document citation returned by future AI retrieval system."""
    document_id: str
    title: str
    document_type: str  # 'pyq' or 'syllabus'
    year: Optional[int] = None
    session: Optional[str] = None
    page_number: Optional[int] = None
    snippet: Optional[str] = None


@dataclass
class AssistantInquiryRequest:
    """Contract for student query sent to the future AI assistant service."""
    message: str
    university_id: Optional[int] = None
    course_id: Optional[int] = None
    branch_id: Optional[int] = None
    semester_id: Optional[int] = None
    subject_id: Optional[int] = None
    requested_format: str = "detailed"  # 'detailed', 'concise', 'formula_first'
    conversation_id: Optional[str] = None
    workflow_intent: str = "general"  # 'find_pyqs', 'exam_prep', 'answer_gen', 'must_prepare'


@dataclass
class AssistantInquiryResponse:
    """Contract for response returned by future AI assistant service."""
    answer_text: str
    status: str  # 'completed', 'pending_integration', 'abstained', 'error'
    sources: List[SourceCitation] = field(default_factory=list)
    model_version: Optional[str] = None
    index_version: Optional[str] = None
    limitations_disclaimer: Optional[str] = None
    abstention_reason: Optional[str] = None


@dataclass
class MustPrepareTopicItem:
    """Contract for subject preparation priority."""
    topic_name: str
    syllabus_unit_id: int
    syllabus_unit_title: str
    priority_level: str  # 'high', 'medium', 'low'
    related_pyq_count: int
    supporting_evidence: str
    historical_frequency_score: float
    limitations: str


@dataclass
class PredictedPaperQuestion:
    """Contract for predicted question item."""
    question_number: str
    question_text: str
    marks: int
    unit_covered: str
    historical_frequency_notes: str


@dataclass
class PredictedPaperResponse:
    """Contract for generated practice paper configuration."""
    paper_title: str
    subject_code: str
    total_marks: int
    duration_minutes: int
    instructions: List[str]
    questions: List[PredictedPaperQuestion]
    topic_coverage: Dict[str, Any]
    limitations_disclaimer: str
    is_simulated_practice_only: bool = True
