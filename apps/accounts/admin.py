from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = "Student Profile"

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (StudentProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Pariksha Role & Permissions", {"fields": ("role",)}),
    )

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "program", "branch", "semester", "enrollment_number", "preferred_answer_format")
    list_filter = ("university", "branch", "semester", "preferred_answer_format")
    search_fields = ("user__username", "user__email", "enrollment_number")
