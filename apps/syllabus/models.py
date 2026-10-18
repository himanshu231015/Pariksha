import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

def syllabus_file_path(instance, filename):
    """Generate safe internal storage path for official syllabus documents."""
    ext = filename.split(".")[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("protected", "syllabus", safe_name)

class SyllabusDocument(models.Model):
    """Official university syllabus curriculum document."""
    AI_STATUS_CHOICES = (
        ("pending_integration", _("Pending Future AI Indexing")),
        ("ready", _("Ready for Model Ingestion")),
        ("not_applicable", _("Archived / Not Applicable")),
    )

    university = models.ForeignKey(
        "academics.University", on_delete=models.CASCADE, related_name="syllabi"
    )
    program = models.ForeignKey(
        "academics.Program", on_delete=models.CASCADE, related_name="syllabi"
    )
    branch = models.ForeignKey(
        "academics.Branch", on_delete=models.CASCADE, related_name="syllabi"
    )
    semester = models.ForeignKey(
        "academics.Semester", on_delete=models.CASCADE, related_name="syllabi"
    )
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.CASCADE, related_name="syllabi"
    )
    academic_year = models.CharField(max_length=20, help_text=_("e.g. 2023-2024"))
    version = models.CharField(max_length=30, default="1.0", help_text=_("e.g. v1.0 or CBGS-2023"))
    title = models.CharField(max_length=255, help_text=_("e.g. CS-501 Operating Systems Official Syllabus"))

    file = models.FileField(upload_to=syllabus_file_path)
    file_size = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_syllabi"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text=_("Official scheme revision details or notes"))
    ai_indexing_status = models.CharField(
        max_length=30, choices=AI_STATUS_CHOICES, default="pending_integration"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Syllabus Document")
        verbose_name_plural = _("Syllabus Documents")
        ordering = ["-academic_year", "-version"]

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"{self.subject.code} Syllabus ({self.version}) - {status}"
