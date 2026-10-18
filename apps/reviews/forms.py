import io
from PIL import Image
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import PaperContribution, ReviewDecision
from apps.papers.models import AcademicPaper
from apps.academics.models import University, Program, Branch, Semester, Subject

def validate_uploaded_file_content(uploaded_file):
    """Enforce strict file type and content inspection (magic bytes & dimensions)."""
    max_bytes = getattr(settings, "MAX_UPLOAD_SIZE", 15 * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise forms.ValidationError(f"File size ({uploaded_file.size // (1024*1024)} MB) exceeds the maximum limit of {max_mb} MB.")

    ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else ""
    allowed_exts = getattr(settings, "ALLOWED_UPLOAD_EXTENSIONS", ["pdf", "png", "jpg", "jpeg"])
    if ext not in allowed_exts:
        raise forms.ValidationError(f"Unsupported file type '.{ext}'. Allowed formats: {', '.join(allowed_exts)}.")

    # Read the file header to verify true content
    uploaded_file.seek(0)
    header = uploaded_file.read(1024)
    uploaded_file.seek(0)

    if ext == "pdf":
        if not header.startswith(b"%PDF-"):
            raise forms.ValidationError("Invalid file content: The uploaded file is not a valid PDF document.")
    elif ext in ("png", "jpg", "jpeg"):
        try:
            image_data = uploaded_file.read()
            uploaded_file.seek(0)
            img = Image.open(io.BytesIO(image_data))
            img.verify()
        except Exception:
            raise forms.ValidationError("Invalid file content: The uploaded image could not be verified.")

    return uploaded_file


class PaperContributionForm(forms.ModelForm):
    """Student submission form with academic consistency and duplicate detection."""
    class Meta:
        model = PaperContribution
        fields = [
            "university",
            "program",
            "branch",
            "semester",
            "subject",
            "exam_year",
            "exam_session",
            "notes",
            "file",
        ]
        widgets = {
            "university": forms.Select(attrs={"class": "form-select", "id": "id_university"}),
            "program": forms.Select(attrs={"class": "form-select", "id": "id_program"}),
            "branch": forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
            "semester": forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
            "subject": forms.Select(attrs={"class": "form-select", "id": "id_subject"}),
            "exam_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2023", "min": 2000, "max": 2030}),
            "exam_session": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "e.g. Clean scanned copy, all 8 questions legible..."}),
            "file": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.png,.jpg,.jpeg"}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            validate_uploaded_file_content(file)
        return file

    def clean(self):
        cleaned_data = super().clean()
        university = cleaned_data.get("university")
        program = cleaned_data.get("program")
        branch = cleaned_data.get("branch")
        semester = cleaned_data.get("semester")
        subject = cleaned_data.get("subject")
        exam_year = cleaned_data.get("exam_year")
        exam_session = cleaned_data.get("exam_session")

        # Academic relationship integrity check
        if branch and program and branch.program != program:
            self.add_error("branch", "Selected branch does not belong to the selected academic program.")

        if semester and program and semester.program != program:
            self.add_error("semester", "Selected semester does not belong to the selected academic program.")

        if subject and branch and subject.branch != branch:
            self.add_error("subject", "Selected subject does not belong to the selected branch.")

        if subject and semester and subject.semester != semester:
            self.add_error("subject", "Selected subject does not belong to the selected semester.")

        # Duplicate detection: Check if an approved AcademicPaper already exists
        if university and program and branch and semester and subject and exam_year and exam_session:
            existing_paper = AcademicPaper.objects.filter(
                university=university,
                program=program,
                branch=branch,
                semester=semester,
                subject=subject,
                exam_year=exam_year,
                exam_session=exam_session,
                is_verified=True,
            ).first()

            if existing_paper:
                self.add_error(
                    None,
                    f"An approved paper for {subject.code} ({exam_session} {exam_year}) is already available in the Pariksha catalog! Paper ID #{existing_paper.id}. You do not need to re-upload it."
                )

            # Check if another pending contribution exists for this exact context
            pending_contribution = PaperContribution.objects.filter(
                university=university,
                program=program,
                branch=branch,
                semester=semester,
                subject=subject,
                exam_year=exam_year,
                exam_session=exam_session,
                status__in=[PaperContribution.STATUS_PENDING, PaperContribution.STATUS_PROCESSING],
            )
            if self.instance and self.instance.pk:
                pending_contribution = pending_contribution.exclude(pk=self.instance.pk)

            if pending_contribution.exists():
                self.add_error(
                    None,
                    f"A paper for {subject.code} ({exam_session} {exam_year}) is already submitted and currently awaiting reviewer verification."
                )

        return cleaned_data


class ReviewActionForm(forms.ModelForm):
    """Form used by authorized reviewers to inspect, modify metadata, and decide on a contribution."""
    university = forms.ModelChoiceField(queryset=University.objects.filter(is_active=True), widget=forms.Select(attrs={"class": "form-select"}))
    program = forms.ModelChoiceField(queryset=Program.objects.filter(is_active=True), widget=forms.Select(attrs={"class": "form-select"}))
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(is_active=True), widget=forms.Select(attrs={"class": "form-select"}))
    semester = forms.ModelChoiceField(queryset=Semester.objects.all(), widget=forms.Select(attrs={"class": "form-select"}))
    subject = forms.ModelChoiceField(queryset=Subject.objects.filter(is_active=True), widget=forms.Select(attrs={"class": "form-select"}))
    exam_year = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    exam_session = forms.ChoiceField(choices=PaperContribution.SESSION_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))

    decision = forms.ChoiceField(
        choices=ReviewDecision.DECISION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select font-monospace fw-bold"}),
    )
    feedback_to_student = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Feedback or reason provided to the student..."}),
    )
    internal_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Internal reviewer notes (audit only)..."}),
    )

    class Meta:
        model = PaperContribution
        fields = [
            "university",
            "program",
            "branch",
            "semester",
            "subject",
            "exam_year",
            "exam_session",
        ]

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        feedback = cleaned_data.get("feedback_to_student", "").strip()

        if decision in (ReviewDecision.DECISION_REJECTED, ReviewDecision.DECISION_NEEDS_CORRECTION) and not feedback:
            self.add_error("feedback_to_student", "Please provide a clear reason or instructions when rejecting or requesting corrections.")

        return cleaned_data
