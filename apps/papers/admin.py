from django.contrib import admin
from .models import AcademicPaper

@admin.register(AcademicPaper)
class AcademicPaperAdmin(admin.ModelAdmin):
    list_display = ("subject", "exam_session", "exam_year", "branch", "semester", "is_verified", "downloads_count", "created_at")
    list_filter = ("is_verified", "exam_year", "exam_session", "branch", "semester")
    search_fields = ("paper_title", "subject__code", "subject__name", "paper_code")
    readonly_fields = ("downloads_count", "created_at", "updated_at")
