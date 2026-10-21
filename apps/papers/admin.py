from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from .models import AcademicPaper


class SolutionStatusFilter(admin.SimpleListFilter):
    title = "Solution Status"
    parameter_name = "solution_status"

    def lookups(self, request, model_admin):
        return (
            ("available", "Solution Available"),
            ("coming_soon", "Coming Soon (No Solution)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "available":
            return queryset.exclude(Q(solution_file="") | Q(solution_file__isnull=True))
        if self.value() == "coming_soon":
            return queryset.filter(Q(solution_file="") | Q(solution_file__isnull=True))
        return queryset


@admin.register(AcademicPaper)
class AcademicPaperAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "exam_session",
        "exam_year",
        "branch",
        "semester",
        "is_verified",
        "solution_status_badge",
        "downloads_count",
        "solution_downloads_count",
        "created_at",
    )
    list_filter = (
        SolutionStatusFilter,
        "is_verified",
        "exam_year",
        "exam_session",
        "branch",
        "semester",
    )
    search_fields = ("paper_title", "subject__code", "subject__name", "paper_code")
    readonly_fields = (
        "downloads_count",
        "solution_downloads_count",
        "solution_file_size",
        "solution_uploaded_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Academic Catalog", {
            "fields": ("university", "program", "branch", "semester", "subject")
        }),
        ("Examination Details", {
            "fields": ("exam_year", "exam_session", "paper_title", "paper_code")
        }),
        ("Question Paper Document", {
            "fields": ("file", "file_size", "file_type", "downloads_count")
        }),
        ("PYQ Solution Document (Admin Upload)", {
            "description": "Upload the official step-by-step verified solution PDF here. Once uploaded, students can view and download it immediately on the paper detail page. If left blank, 'Coming Soon' is displayed to students.",
            "fields": (
                "solution_file",
                "solution_uploaded_by",
                "solution_uploaded_at",
                "solution_file_size",
                "solution_file_type",
                "solution_downloads_count",
            ),
        }),
        ("Verification & Audit", {
            "fields": ("is_verified", "contributor", "verified_by", "created_at", "updated_at")
        }),
    )

    @admin.display(description="Solution")
    def solution_status_badge(self, obj):
        if obj.has_solution:
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0f5132; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">✓ Available</span>'
            )
        return format_html(
            '<span style="background-color: #fff3cd; color: #664d03; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">⏳ Coming Soon</span>'
        )

    def save_model(self, request, obj, form, change):
        if "solution_file" in form.changed_data and obj.solution_file:
            obj.solution_uploaded_by = request.user
            from django.utils import timezone
            obj.solution_uploaded_at = timezone.now()
        super().save_model(request, obj, form, change)

