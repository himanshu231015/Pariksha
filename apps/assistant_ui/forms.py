from django import forms
from apps.academics.models import University, Program, Branch, Semester, Subject

class AskParikshaForm(forms.Form):
    """Academic question and assistant context configuration form."""
    FORMAT_CHOICES = (
        ("detailed", "Detailed Exam Steps & Diagrams"),
        ("concise", "Concise Bullet Points & Summaries"),
        ("formula_first", "Formulas & Mathematical Derivations First"),
    )

    INTENT_CHOICES = (
        ("general", "General Academic Inquiry"),
        ("find_pyqs", "Locate Relevant PYQ Questions"),
        ("exam_prep", "Exam-Oriented Concept Preparation"),
        ("answer_gen", "Format Model 7-Mark Answer"),
        ("must_prepare", "Highlight Crucial Topic Weightage"),
    )

    university = forms.ModelChoiceField(
        queryset=University.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_university"}),
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_program"}),
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_subject"}),
    )
    requested_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="detailed",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    workflow_intent = forms.ChoiceField(
        choices=INTENT_CHOICES,
        initial="exam_prep",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Ask an RGPV exam preparation question, e.g., 'Explain CPU Scheduling algorithms with Gantt chart for 7 marks'...",
            }
        ),
        required=False,
    )


class PredictedPaperConfigForm(forms.Form):
    """Configuration form for generating practice test papers."""
    university = forms.ModelChoiceField(
        queryset=University.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_university"}),
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_program"}),
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_subject"}),
    )
    total_marks = forms.IntegerField(
        initial=70,
        min_value=20,
        max_value=100,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Standard RGPV end-semester theoretical paper is 70 marks",
    )
    duration_minutes = forms.IntegerField(
        initial=180,
        min_value=30,
        max_value=240,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Standard RGPV exam duration is 180 minutes (3 hours)",
    )


class MustPrepareFilterForm(forms.Form):
    """Subject selector for topic weightage and preparation priorities."""
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_subject"}),
    )
