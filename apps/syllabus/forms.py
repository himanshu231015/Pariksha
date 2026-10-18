from django import forms
from .models import SyllabusDocument
from apps.reviews.forms import validate_uploaded_file_content

class SyllabusUploadForm(forms.ModelForm):
    """Admin form for uploading and cataloging official curriculum documents."""
    class Meta:
        model = SyllabusDocument
        fields = [
            "university",
            "program",
            "branch",
            "semester",
            "subject",
            "academic_year",
            "version",
            "title",
            "is_published",
            "notes",
            "file",
        ]
        widgets = {
            "university": forms.Select(attrs={"class": "form-select", "id": "id_university"}),
            "program": forms.Select(attrs={"class": "form-select", "id": "id_program"}),
            "branch": forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
            "semester": forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
            "subject": forms.Select(attrs={"class": "form-select", "id": "id_subject"}),
            "academic_year": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 2023-2024"}),
            "version": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. v2.1 or CBGS-2023"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Scheme & Detailed Syllabus - CS501"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Scheme revision remarks..."}),
            "file": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf"}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            validate_uploaded_file_content(file)
            ext = file.name.split(".")[-1].lower()
            if ext != "pdf":
                raise forms.ValidationError("Official syllabus documents must be in PDF format.")
        return file
