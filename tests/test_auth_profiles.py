from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import StudentProfile
from apps.accounts.forms import StudentProfileForm
from apps.academics.models import University, Program, Branch, Semester

User = get_user_model()

class AuthenticationAndProfilesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.university = University.objects.create(name="RGPV Bhopal", code="RGPV")
        self.program = Program.objects.create(university=self.university, name="B.Tech", code="B.Tech")
        self.branch_cse = Branch.objects.create(program=self.program, name="CSE", code="CSE")
        self.semester_5 = Semester.objects.create(program=self.program, number=5, title="Semester 5")

        self.student = User.objects.create_user(
            username="test_student",
            email="test_student@pariksha.edu",
            password="testpassword123",
            role=User.ROLE_STUDENT,
        )

    def test_signup_page_renders_and_creates_student(self):
        """Signup page loads and allows new student registration."""
        res = self.client.get(reverse("accounts:signup"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Create Student Account")

        signup_data = {
            "first_name": "Rohan",
            "last_name": "Verma",
            "username": "rohan_v",
            "email": "rohan@pariksha.edu",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        res_post = self.client.post(reverse("accounts:signup"), signup_data)
        self.assertEqual(res_post.status_code, 302)
        self.assertTrue(User.objects.filter(username="rohan_v").exists())

    def test_anonymous_users_redirected_from_protected_pages(self):
        """Anonymous users must not access private dashboard and profile views."""
        protected_urls = [
            reverse("assistant_ui:dashboard"),
            reverse("accounts:profile"),
            reverse("reviews:contribute"),
            reverse("reviews:my_contributions"),
            reverse("papers:list"),
            reverse("assistant_ui:chat"),
            reverse("assistant_ui:must_prepare"),
            reverse("assistant_ui:predicted_paper"),
            reverse("syllabus:list"),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_profile_auto_created_on_user_creation(self):
        """Signal must ensure every User has an associated StudentProfile."""
        self.assertTrue(hasattr(self.student, "student_profile"))
        self.assertIsInstance(self.student.student_profile, StudentProfile)

    def test_student_profile_update(self):
        """Authenticated student can update preferences and display details."""
        self.client.login(username="test_student", password="testpassword123")
        post_data = {
            "first_name": "Aarav",
            "last_name": "Patel",
            "university": self.university.id,
            "program": self.program.id,
            "branch": self.branch_cse.id,
            "semester": self.semester_5.id,
            "enrollment_number": "0101CS211001",
            "expected_graduation_year": 2026,
            "preferred_answer_format": "detailed",
            "bio": "Specializing in Distributed Systems",
        }
        response = self.client.post(reverse("accounts:profile"), post_data)
        self.assertEqual(response.status_code, 302)

        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, "Aarav")
        profile = self.student.student_profile
        self.assertEqual(profile.branch, self.branch_cse)
        self.assertEqual(profile.enrollment_number, "0101CS211001")
        self.assertTrue(profile.is_complete)

    def test_inconsistent_academic_catalog_selection_rejected(self):
        """Branch belonging to Program A cannot be assigned with Program B."""
        prog_other = Program.objects.create(university=self.university, name="M.Tech", code="M.Tech")
        branch_other = Branch.objects.create(program=prog_other, name="VLSI", code="VLSI")

        form = StudentProfileForm(
            data={
                "first_name": "Aarav",
                "university": self.university.id,
                "program": self.program.id,      # B.Tech
                "branch": branch_other.id,       # Belongs to M.Tech!
                "semester": self.semester_5.id,
                "preferred_answer_format": "detailed",
            },
            instance=self.student.student_profile,
            user=self.student,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("branch", form.errors)

    def test_student_cannot_elevate_own_role(self):
        """Students cannot alter their role through profile form submissions."""
        self.client.login(username="test_student", password="testpassword123")
        post_data = {
            "first_name": "Aarav",
            "role": User.ROLE_ADMIN,  # Tampering attempt
            "is_staff": True,
            "is_superuser": True,
        }
        self.client.post(reverse("accounts:profile"), post_data)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.ROLE_STUDENT)
        self.assertFalse(self.student.is_staff)
        self.assertFalse(self.student.is_superuser)

    def test_login_success_redirects_to_dashboard_by_default(self):
        """Login without next query parameter redirects to assistant_ui:dashboard."""
        res = self.client.post(
            reverse("accounts:login"),
            {"username": "test_student", "password": "testpassword123"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse("assistant_ui:dashboard"))

    def test_authenticated_user_accessing_login_or_signup_redirected_to_dashboard(self):
        """Logged-in users visiting login or signup page are redirected to dashboard."""
        self.client.login(username="test_student", password="testpassword123")
        res_login = self.client.get(reverse("accounts:login"))
        self.assertEqual(res_login.status_code, 302)
        self.assertEqual(res_login.url, reverse("assistant_ui:dashboard"))

        res_signup = self.client.get(reverse("accounts:signup"))
        self.assertEqual(res_signup.status_code, 302)
        self.assertEqual(res_signup.url, reverse("assistant_ui:dashboard"))
