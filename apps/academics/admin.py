from django.contrib import admin
from .models import University, Program, Branch, Semester, Subject, SyllabusUnit

class SyllabusUnitInline(admin.TabularInline):
    model = SyllabusUnit
    extra = 1

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "short_name", "location", "is_active")
    search_fields = ("name", "code", "short_name")

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "university", "total_semesters", "is_active")
    list_filter = ("university", "is_active")

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "program", "is_active")
    list_filter = ("program", "is_active")
    search_fields = ("name", "code")

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("title", "number", "program")
    list_filter = ("program",)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "branch", "semester", "credits", "is_active")
    list_filter = ("branch", "semester", "is_active")
    search_fields = ("code", "name")
    inlines = [SyllabusUnitInline]

@admin.register(SyllabusUnit)
class SyllabusUnitAdmin(admin.ModelAdmin):
    list_display = ("subject", "unit_number", "title")
    list_filter = ("subject__branch", "subject__semester")
    search_fields = ("title", "subject__name", "subject__code")
