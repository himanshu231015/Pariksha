from django.contrib import admin
from .models import SyllabusDocument

@admin.register(SyllabusDocument)
class SyllabusDocumentAdmin(admin.ModelAdmin):
    list_display = ("subject", "version", "academic_year", "branch", "semester", "is_published", "published_at", "uploaded_by")
    list_filter = ("is_published", "academic_year", "branch", "semester", "ai_indexing_status")
    search_fields = ("title", "subject__code", "subject__name", "version")
