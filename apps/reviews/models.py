import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

def contribution_file_path(instance, filename):
    """Generate safe internal storage path for contributed papers awaiting review."""
    ext = filename.split(".")[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("protected", "contributions", safe_name)

class PaperContribution(models.Model):
    """Student-submitted examination paper awaiting reviewer verification."""
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_NEEDS_CORRECTION = "needs_correction"
    STATUS_DUPLICATE = "duplicate"

    STATUS_CHOICES = (
        (STATUS_PENDING, _("Pending Review")),
        (STATUS_PROCESSING, _("Under Review")),
        (STATUS_APPROVED, _("Approved & Published")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_NEEDS_CORRECTION, _("Needs Correction")),
        (STATUS_DUPLICATE, _("Marked Duplicate")),
    )

    SESSION_CHOICES = (
        ("Nov-Dec", _("November - December (Winter/End Sem)")),
        ("May-June", _("May - June (Summer/Even Sem)")),
        ("Special", _("Special / Supplementary Examination")),
    )

    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contributions"
    )
    university = models.ForeignKey(
        "academics.University", on_delete=models.CASCADE, related_name="contributions"
    )
    program = models.ForeignKey(
        "academics.Program", on_delete=models.CASCADE, related_name="contributions"
    )
    branch = models.ForeignKey(
        "academics.Branch", on_delete=models.CASCADE, related_name="contributions"
    )
    semester = models.ForeignKey(
        "academics.Semester", on_delete=models.CASCADE, related_name="contributions"
    )
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.CASCADE, related_name="contributions"
    )
    exam_year = models.PositiveSmallIntegerField(help_text=_("e.g. 2023 or 2024"))
    exam_session = models.CharField(max_length=30, choices=SESSION_CHOICES, default="Nov-Dec")
    paper_title = models.CharField(max_length=255, blank=True)

    file = models.FileField(upload_to=contribution_file_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    file_type = models.CharField(max_length=100, default="application/pdf")
    notes = models.TextField(blank=True, help_text=_("Optional notes from student about paper condition, missing pages, etc."))

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Paper Contribution")
        verbose_name_plural = _("Paper Contributions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject.code} ({self.exam_session} {self.exam_year}) by {self.contributor.username}"

    @property
    def is_editable_by_student(self):
        return self.status in (self.STATUS_NEEDS_CORRECTION, self.STATUS_PENDING)

    @property
    def file_extension(self):
        if self.file and self.file.name:
            return self.file.name.split(".")[-1].upper()
        return "FILE"


class ReviewDecision(models.Model):
    """Review decision record for an uploaded paper contribution."""
    DECISION_APPROVED = "approved"
    DECISION_REJECTED = "rejected"
    DECISION_NEEDS_CORRECTION = "needs_correction"
    DECISION_DUPLICATE = "duplicate"

    DECISION_CHOICES = (
        (DECISION_APPROVED, _("Approved")),
        (DECISION_REJECTED, _("Rejected")),
        (DECISION_NEEDS_CORRECTION, _("Requested Corrections")),
        (DECISION_DUPLICATE, _("Marked as Duplicate")),
    )

    contribution = models.ForeignKey(
        PaperContribution, on_delete=models.CASCADE, related_name="review_history"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_conducted"
    )
    decision = models.CharField(max_length=30, choices=DECISION_CHOICES)
    feedback_to_student = models.TextField(
        blank=True, help_text=_("Explanation or correction notes visible to the student contributor")
    )
    internal_notes = models.TextField(blank=True, help_text=_("Internal reviewer-only notes"))
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Review Decision")
        verbose_name_plural = _("Review Decisions")
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"{self.get_decision_display()} on #{self.contribution.id} by {self.reviewer.username}"


class AuditLog(models.Model):
    """System-wide audit trail of review and administrative actions."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-timestamp"]

    def __str__(self):
        actor = self.user.username if self.user else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} - {self.action} on {self.target_type}:{self.target_id}"
