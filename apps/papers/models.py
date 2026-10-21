import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

def paper_file_path(instance, filename):
    """Generate safe internal storage path for approved academic papers."""
    ext = filename.split(".")[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("protected", "papers", safe_name)

def solution_file_path(instance, filename):
    """Generate safe internal storage path for approved academic paper solutions."""
    ext = filename.split(".")[-1].lower()
    safe_name = f"solution_{uuid.uuid4().hex}.{ext}"
    return os.path.join("protected", "solutions", safe_name)

class AcademicPaper(models.Model):
    """Verified, approved examination question paper."""
    SESSION_CHOICES = (
        ("Nov-Dec", _("November - December (Winter/End Sem)")),
        ("May-June", _("May - June (Summer/Even Sem)")),
        ("Special", _("Special / Supplementary Examination")),
    )

    university = models.ForeignKey(
        "academics.University", on_delete=models.CASCADE, related_name="papers"
    )
    program = models.ForeignKey(
        "academics.Program", on_delete=models.CASCADE, related_name="papers"
    )
    branch = models.ForeignKey(
        "academics.Branch", on_delete=models.CASCADE, related_name="papers"
    )
    semester = models.ForeignKey(
        "academics.Semester", on_delete=models.CASCADE, related_name="papers"
    )
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.CASCADE, related_name="papers"
    )
    exam_year = models.PositiveSmallIntegerField(help_text=_("e.g. 2023 or 2024"))
    exam_session = models.CharField(max_length=30, choices=SESSION_CHOICES, default="Nov-Dec")
    paper_title = models.CharField(max_length=255, help_text=_("e.g. CS-501 Operating Systems Dec 2023"))
    paper_code = models.CharField(max_length=50, blank=True, help_text=_("Internal paper code / QP code if available"))

    file = models.FileField(upload_to=paper_file_path, help_text=_("Protected paper document"))
    file_size = models.PositiveIntegerField(default=0, help_text=_("Size in bytes"))
    file_type = models.CharField(max_length=50, default="application/pdf")

    # PYQ Solution document uploaded by admin/faculty
    solution_file = models.FileField(
        upload_to=solution_file_path,
        null=True,
        blank=True,
        help_text=_("Protected paper solution document (PDF) uploaded by administrator")
    )
    solution_file_size = models.PositiveIntegerField(default=0, help_text=_("Solution size in bytes"))
    solution_file_type = models.CharField(max_length=50, default="application/pdf")
    solution_uploaded_at = models.DateTimeField(null=True, blank=True, help_text=_("Timestamp when solution was uploaded"))
    solution_uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_solutions"
    )
    solution_downloads_count = models.PositiveIntegerField(default=0)

    is_verified = models.BooleanField(default=True)
    verification_date = models.DateTimeField(auto_now_add=True)
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="contributed_papers"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_papers"
    )
    downloads_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Academic Paper (PYQ)")
        unique_together = ("university", "program", "branch", "semester", "subject", "exam_year", "exam_session")
        ordering = ["-exam_year", "-id"]

    def __str__(self):
        return f"{self.subject.code} ({self.exam_session} {self.exam_year})"

    @property
    def file_extension(self):
        if self.file and self.file.name:
            return self.file.name.split(".")[-1].upper()
        return "PDF"

    @property
    def has_solution(self):
        """Check if an approved solution file exists for this paper."""
        return bool(self.solution_file and self.solution_file.name)

    @property
    def solution_file_extension(self):
        if self.solution_file and self.solution_file.name:
            return self.solution_file.name.split(".")[-1].upper()
        return "PDF"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.solution_file:
            try:
                self.solution_file_size = self.solution_file.size
            except Exception:
                pass
            if not self.solution_uploaded_at:
                self.solution_uploaded_at = timezone.now()
        super().save(*args, **kwargs)
