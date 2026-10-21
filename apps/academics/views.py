from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import University, Program, Branch, Semester, Subject, SyllabusUnit

@login_required
@require_GET
def api_programs(request):
    """Return JSON list of programs for a given university."""
    university_id = request.GET.get("university_id")
    qs = Program.objects.filter(is_active=True)
    if university_id:
        qs = qs.filter(university_id=university_id)
    data = [{"id": p.id, "name": p.name, "code": p.code} for p in qs]
    return JsonResponse({"programs": data})

@login_required
@require_GET
def api_branches(request):
    """Return JSON list of branches for a given program."""
    program_id = request.GET.get("program_id")
    qs = Branch.objects.filter(is_active=True)
    if program_id:
        qs = qs.filter(program_id=program_id)
    data = [{"id": b.id, "name": b.name, "code": b.code} for b in qs]
    return JsonResponse({"branches": data})

@login_required
@require_GET
def api_semesters(request):
    """Return JSON list of semesters for a given program."""
    program_id = request.GET.get("program_id")
    qs = Semester.objects.all()
    if program_id:
        qs = qs.filter(program_id=program_id)
    data = [{"id": s.id, "number": s.number, "title": s.title} for s in qs]
    return JsonResponse({"semesters": data})

@login_required
@require_GET
def api_subjects(request):
    """Return JSON list of subjects filtered by branch and semester."""
    branch_id = request.GET.get("branch_id")
    semester_id = request.GET.get("semester_id")
    qs = Subject.objects.filter(is_active=True)
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    data = [{"id": s.id, "code": s.code, "name": s.name} for s in qs]
    return JsonResponse({"subjects": data})

@login_required
@require_GET
def api_units(request):
    """Return JSON list of syllabus units for a subject."""
    subject_id = request.GET.get("subject_id")
    qs = SyllabusUnit.objects.all()
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    data = [{"id": u.id, "unit_number": u.unit_number, "title": u.title, "description": u.description} for u in qs]
    return JsonResponse({"units": data})
