from django.contrib import admin
from .models import PaperContribution, ReviewDecision, AuditLog

class ReviewDecisionInline(admin.TabularInline):
    model = ReviewDecision
    extra = 0
    readonly_fields = ("reviewer", "decision", "feedback_to_student", "internal_notes", "reviewed_at")

@admin.register(PaperContribution)
class PaperContributionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "exam_session", "exam_year", "contributor", "status", "created_at")
    list_filter = ("status", "exam_year", "exam_session", "branch")
    search_fields = ("subject__code", "subject__name", "contributor__username")
    inlines = [ReviewDecisionInline]
    readonly_fields = ("original_filename", "file_size", "file_type", "created_at", "updated_at")

@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("contribution", "reviewer", "decision", "reviewed_at")
    list_filter = ("decision", "reviewed_at")
    search_fields = ("reviewer__username", "contribution__subject__code")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "target_type", "target_id", "ip_address")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "action", "target_type", "details")
    readonly_fields = ("timestamp",)
