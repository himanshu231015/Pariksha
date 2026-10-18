from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model for Pariksha supporting explicit roles."""
    ROLE_STUDENT = "student"
    ROLE_REVIEWER = "reviewer"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = (
        (ROLE_STUDENT, _("Student")),
        (ROLE_REVIEWER, _("Reviewer")),
        (ROLE_ADMIN, _("Administrator")),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT or self.is_superuser

    @property
    def is_reviewer(self):
        return self.role in (self.ROLE_REVIEWER, self.ROLE_ADMIN) or self.is_staff or self.is_superuser

    @property
    def is_administrator(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} ({self.get_role_display()})"


class StudentProfile(models.Model):
    """Academic preferences and profile configuration for a student."""
    FORMAT_CONCISE = "concise"
    FORMAT_DETAILED = "detailed"
    FORMAT_FORMULA = "formula_first"

    FORMAT_CHOICES = (
        (FORMAT_DETAILED, _("Detailed Exam Steps & Diagrams")),
        (FORMAT_CONCISE, _("Concise Bullet Points & Summaries")),
        (FORMAT_FORMULA, _("Formula-First & Mathematical Derivations")),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    university = models.ForeignKey(
        "academics.University", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    program = models.ForeignKey(
        "academics.Program", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    branch = models.ForeignKey(
        "academics.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    semester = models.ForeignKey(
        "academics.Semester", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    enrollment_number = models.CharField(max_length=50, blank=True, help_text=_("e.g. 0101CS211045"))
    expected_graduation_year = models.PositiveIntegerField(null=True, blank=True)
    preferred_answer_format = models.CharField(max_length=30, choices=FORMAT_CHOICES, default=FORMAT_DETAILED)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def is_complete(self):
        """Check whether basic academic context is established."""
        return bool(self.university and self.branch and self.semester)
