from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import StudentProfile
from apps.academics.models import University, Program, Branch, Semester

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """User registration form with email requirement."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "student@university.edu"}))
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}))
    last_name = forms.CharField(required=False, max_length=30, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.role = User.ROLE_STUDENT  # Explicitly force student role
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Clean sign-in form with bootstrap styling."""
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username or Email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))


class StudentProfileForm(forms.ModelForm):
    """Student profile and academic preferences editing form."""
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = StudentProfile
        fields = [
            "university",
            "program",
            "branch",
            "semester",
            "enrollment_number",
            "expected_graduation_year",
            "preferred_answer_format",
            "avatar",
            "bio",
        ]
        widgets = {
            "university": forms.Select(attrs={"class": "form-select", "id": "id_university"}),
            "program": forms.Select(attrs={"class": "form-select", "id": "id_program"}),
            "branch": forms.Select(attrs={"class": "form-select", "id": "id_branch"}),
            "semester": forms.Select(attrs={"class": "form-select", "id": "id_semester"}),
            "enrollment_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 0101CS211045"}),
            "expected_graduation_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2026"}),
            "preferred_answer_format": forms.Select(attrs={"class": "form-select"}),
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Brief academic interests or subjects..."}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name

    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get("program")
        branch = cleaned_data.get("branch")
        semester = cleaned_data.get("semester")

        # Validate academic relationship consistency
        if branch and program and branch.program != program:
            self.add_error("branch", "Selected branch does not belong to the selected academic program.")

        if semester and program and semester.program != program:
            self.add_error("semester", "Selected semester does not belong to the selected academic program.")

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.last_name = self.cleaned_data["last_name"]
            self.user.save()
        if commit:
            profile.save()
        return profile
