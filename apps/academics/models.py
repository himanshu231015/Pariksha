from django.db import models
from django.utils.translation import gettext_lazy as _

class University(models.Model):
    """Accredited University or Academic Board."""
    name = models.CharField(max_length=255, help_text=_("Official University Name, e.g. Rajiv Gandhi Proudyogiki Vishwavidyalaya"))
    short_name = models.CharField(max_length=100, help_text=_("Common short name, e.g. RGPV Bhopal"))
    code = models.CharField(max_length=20, unique=True, help_text=_("Unique identifier code, e.g. RGPV"))
    location = models.CharField(max_length=255, blank=True, help_text=_("City, State, Country"))
    website = models.URLField(blank=True, help_text=_("Official portal URL"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("University")
        verbose_name_plural = _("Universities")
        ordering = ["name"]

    def __str__(self):
        return f"{self.short_name} ({self.code})"


class Program(models.Model):
    """Academic degree course or program (e.g. B.Tech)."""
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="programs")
    name = models.CharField(max_length=150, help_text=_("e.g. Bachelor of Technology"))
    code = models.CharField(max_length=30, help_text=_("e.g. B.Tech"))
    total_semesters = models.PositiveSmallIntegerField(default=8)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Program / Course")
        verbose_name_plural = _("Programs & Courses")
        unique_together = ("university", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.university.code}"


class Branch(models.Model):
    """Academic discipline / specialization (e.g. CSE, IT, ME)."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=150, help_text=_("e.g. Computer Science & Engineering"))
    code = models.CharField(max_length=20, help_text=_("e.g. CSE"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        unique_together = ("program", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Semester(models.Model):
    """Academic semester level (e.g. 1st Semester to 8th Semester)."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="semesters")
    number = models.PositiveSmallIntegerField(help_text=_("Semester number (1-8)"))
    title = models.CharField(max_length=50, help_text=_("e.g. Semester V or 5th Semester"))

    class Meta:
        verbose_name = _("Semester")
        verbose_name_plural = _("Semesters")
        unique_together = ("program", "number")
        ordering = ["number"]

    def __str__(self):
        return f"{self.title} ({self.program.code})"


class Subject(models.Model):
    """Individual subject / course unit."""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="subjects")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="subjects")
    code = models.CharField(max_length=30, help_text=_("Official subject code, e.g. CS-501"))
    name = models.CharField(max_length=255, help_text=_("e.g. Data Communication"))
    credits = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")
        unique_together = ("branch", "semester", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class SyllabusUnit(models.Model):
    """Curriculum unit within a subject."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="units")
    unit_number = models.PositiveSmallIntegerField(help_text=_("Unit number (1-5)"))
    title = models.CharField(max_length=255, help_text=_("e.g. Unit 1: Physical Layer & Signal Transmission"))
    description = models.TextField(blank=True, help_text=_("Key topics and learning objectives covered in this unit"))

    class Meta:
        verbose_name = _("Syllabus Unit")
        verbose_name_plural = _("Syllabus Units")
        unique_together = ("subject", "unit_number")
        ordering = ["unit_number"]

    def __str__(self):
        return f"{self.subject.code} - Unit {self.unit_number}: {self.title}"
