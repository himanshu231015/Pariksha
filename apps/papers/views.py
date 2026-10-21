import os
import mimetypes
from collections import OrderedDict
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.clickjacking import xframe_options_sameorigin
from .models import AcademicPaper
from apps.academics.models import University, Program, Branch, Semester, Subject

@login_required
def paper_list(request):
    """Search and filter verified PYQs (Page 5)."""
    universities = University.objects.filter(is_active=True)
    programs = Program.objects.filter(is_active=True)
    branches = Branch.objects.filter(is_active=True)
    semesters = Semester.objects.all()

    # Preselect defaults from profile if user has one and no GET parameters were supplied
    initial_branch_id = None
    initial_semester_id = None
    if request.user.is_authenticated and not request.GET:
        profile = getattr(request.user, "student_profile", None)
        if profile and profile.branch:
            initial_branch_id = profile.branch.id
        if profile and profile.semester:
            initial_semester_id = profile.semester.id

    university_id = request.GET.get("university")
    program_id = request.GET.get("program")
    branch_id = request.GET.get("branch") or initial_branch_id
    semester_id = request.GET.get("semester") or initial_semester_id
    subject_id = request.GET.get("subject")
    exam_year = request.GET.get("year")
    exam_session = request.GET.get("session")
    search_query = request.GET.get("q", "").strip()

    # Only show verified papers in public search
    papers_qs = AcademicPaper.objects.filter(is_verified=True).select_related(
        "university", "program", "branch", "semester", "subject"
    )

    if university_id:
        papers_qs = papers_qs.filter(university_id=university_id)
    if program_id:
        papers_qs = papers_qs.filter(program_id=program_id)
    if branch_id:
        papers_qs = papers_qs.filter(branch_id=branch_id)
    if semester_id:
        papers_qs = papers_qs.filter(semester_id=semester_id)
    if subject_id:
        papers_qs = papers_qs.filter(subject_id=subject_id)
    if exam_year:
        papers_qs = papers_qs.filter(exam_year=exam_year)
    if exam_session:
        papers_qs = papers_qs.filter(exam_session=exam_session)
    if search_query:
        papers_qs = papers_qs.filter(
            Q(paper_title__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(subject__code__icontains=search_query) |
            Q(paper_code__icontains=search_query)
        )

    # Available subjects for filtering (optionally scoped to selected branch/semester)
    subjects_qs = Subject.objects.filter(is_active=True)
    if branch_id:
        subjects_qs = subjects_qs.filter(branch_id=branch_id)
    if semester_id:
        subjects_qs = subjects_qs.filter(semester_id=semester_id)

    # Distinct examination years present in database
    available_years = (
        AcademicPaper.objects.filter(is_verified=True)
        .values_list("exam_year", flat=True)
        .distinct()
        .order_by("-exam_year")
    )

    # Group verified papers by subject so each card represents a Subject with all its available papers
    subject_map = OrderedDict()
    for paper in papers_qs:
        sub_id = paper.subject_id
        if sub_id not in subject_map:
            subject_map[sub_id] = {
                "subject": paper.subject,
                "branch": paper.branch,
                "semester": paper.semester,
                "university": paper.university,
                "latest_paper": paper,
                "papers": [],
                "total_downloads": 0,
            }
        subject_map[sub_id]["papers"].append(paper)
        subject_map[sub_id]["total_downloads"] += paper.downloads_count

    # Fetch all verified papers for these subjects so clicking Details shows all papers of that subject
    subject_ids = list(subject_map.keys())
    all_papers_for_subjects = (
        AcademicPaper.objects.filter(subject_id__in=subject_ids, is_verified=True)
        .select_related("subject", "branch", "semester", "university")
        .order_by("-exam_year", "-id")
    )
    all_papers_by_subject = {}
    for p in all_papers_for_subjects:
        all_papers_by_subject.setdefault(p.subject_id, []).append(p)

    for sub_id, item in subject_map.items():
        item["all_papers"] = all_papers_by_subject.get(sub_id, item["papers"])
        item["solutions_count"] = sum(1 for p in item["all_papers"] if p.has_solution)

    subject_cards = list(subject_map.values())
    paginator = Paginator(subject_cards, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "subject_cards": page_obj.object_list,
        "papers": page_obj.object_list,
        "total_results": papers_qs.count(),
        "total_subjects": len(subject_cards),
        "universities": universities,
        "programs": programs,
        "branches": branches,
        "semesters": semesters,
        "subjects": subjects_qs,
        "available_years": available_years,
        "selected_university": str(university_id) if university_id else "",
        "selected_program": str(program_id) if program_id else "",
        "selected_branch": str(branch_id) if branch_id else "",
        "selected_semester": str(semester_id) if semester_id else "",
        "selected_subject": str(subject_id) if subject_id else "",
        "selected_year": str(exam_year) if exam_year else "",
        "selected_session": str(exam_session) if exam_session else "",
        "search_query": search_query,
    }
    return render(request, "papers/list.html", context)


@login_required
def subject_papers(request, subject_id):
    """View showing all verified question papers for a specific subject with dates and codes."""
    subject = get_object_or_404(
        Subject.objects.select_related("branch", "semester", "branch__program", "branch__program__university"),
        pk=subject_id,
        is_active=True,
    )

    papers = (
        AcademicPaper.objects.filter(subject=subject, is_verified=True)
        .select_related("university", "program", "branch", "semester", "subject")
        .order_by("-exam_year", "-id")
    )

    total_downloads = sum(p.downloads_count for p in papers)

    context = {
        "subject": subject,
        "papers": papers,
        "total_papers": papers.count(),
        "total_downloads": total_downloads,
    }
    return render(request, "papers/subject_papers.html", context)


@login_required
def paper_detail(request, pk):
    """Detailed view for a specific verified question paper (Page 6)."""
    paper = get_object_or_404(
        AcademicPaper.objects.select_related("university", "program", "branch", "semester", "subject", "contributor"),
        pk=pk,
        is_verified=True,
    )

    # All verified papers for the same subject across other years/sessions
    all_subject_papers = (
        AcademicPaper.objects.filter(subject=paper.subject, is_verified=True)
        .order_by("-exam_year", "-id")
    )
    related_papers = [p for p in all_subject_papers if p.pk != paper.pk]
    total_downloads = sum(p.downloads_count for p in all_subject_papers)

    context = {
        "paper": paper,
        "all_subject_papers": all_subject_papers,
        "related_papers": related_papers,
        "total_downloads": total_downloads,
    }
    return render(request, "papers/detail.html", context)


@login_required
def paper_download(request, pk):
    """Authorized download view for verified question papers."""
    paper = get_object_or_404(AcademicPaper, pk=pk, is_verified=True)

    if not paper.file or not os.path.exists(paper.file.path):
        raise Http404("The requested paper document file is currently unavailable on disk.")

    # Increment download counter
    paper.downloads_count += 1
    paper.save(update_fields=["downloads_count"])

    # Determine filename
    safe_filename = f"{paper.subject.code}_{paper.exam_session}_{paper.exam_year}.{paper.file_extension.lower()}"
    content_type, _ = mimetypes.guess_type(paper.file.path)

    response = FileResponse(open(paper.file.path, "rb"), content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
    return response


@xframe_options_sameorigin
@login_required
def paper_preview(request, pk):
    """Safe inline preview of the document."""
    paper = get_object_or_404(AcademicPaper, pk=pk, is_verified=True)

    if not paper.file or not os.path.exists(paper.file.path):
        raise Http404("Document file not found.")

    content_type, _ = mimetypes.guess_type(paper.file.path)
    response = FileResponse(open(paper.file.path, "rb"), content_type=content_type or "application/pdf")
    response["Content-Disposition"] = "inline"
    return response


@login_required
def solution_download(request, pk):
    """Authorized download view for PYQ solutions."""
    paper = get_object_or_404(AcademicPaper, pk=pk, is_verified=True)

    if not paper.has_solution or not paper.solution_file or not os.path.exists(paper.solution_file.path):
        raise Http404("The requested paper solution is coming soon and not yet available on disk.")

    # Increment solution download counter
    paper.solution_downloads_count += 1
    paper.save(update_fields=["solution_downloads_count"])

    # Determine filename
    safe_filename = f"{paper.subject.code}_{paper.exam_session}_{paper.exam_year}_Solution.{paper.solution_file_extension.lower()}"
    content_type, _ = mimetypes.guess_type(paper.solution_file.path)

    response = FileResponse(open(paper.solution_file.path, "rb"), content_type=content_type or "application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
    return response


@xframe_options_sameorigin
@login_required
def solution_preview(request, pk):
    """Safe inline preview of the PYQ solution."""
    paper = get_object_or_404(AcademicPaper, pk=pk, is_verified=True)

    if not paper.has_solution or not paper.solution_file or not os.path.exists(paper.solution_file.path):
        raise Http404("Solution document not found or coming soon.")

    content_type, _ = mimetypes.guess_type(paper.solution_file.path)
    response = FileResponse(open(paper.solution_file.path, "rb"), content_type=content_type or "application/pdf")
    response["Content-Disposition"] = "inline"
    return response


@login_required
def upload_solution(request, pk):
    """Administrator / Reviewer direct upload of PYQ solution from detail page."""
    paper = get_object_or_404(AcademicPaper, pk=pk)

    is_authorized = (
        request.user.is_superuser
        or request.user.is_staff
        or getattr(request.user, "is_administrator", False)
        or getattr(request.user, "is_reviewer", False)
    )
    if not is_authorized:
        return HttpResponseForbidden("Only administrators and verified reviewers can upload paper solutions.")

    if request.method == "POST":
        solution_file = request.FILES.get("solution_file")
        if not solution_file:
            messages.error(request, "Please choose a solution file (PDF) to upload.")
            return redirect("papers:detail", pk=pk)

        ext = solution_file.name.split(".")[-1].lower()
        allowed_extensions = getattr(settings, "ALLOWED_UPLOAD_EXTENSIONS", ["pdf", "png", "jpg", "jpeg"])
        if ext not in allowed_extensions:
            messages.error(request, f"File format .{ext} is not allowed. Please upload a PDF or image document.")
            return redirect("papers:detail", pk=pk)

        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 15 * 1024 * 1024)
        if solution_file.size > max_size:
            messages.error(request, "File size exceeds the allowed limit.")
            return redirect("papers:detail", pk=pk)

        paper.solution_file = solution_file
        paper.solution_file_size = solution_file.size
        paper.solution_file_type = solution_file.content_type or "application/pdf"
        paper.solution_uploaded_by = request.user
        paper.solution_uploaded_at = timezone.now()
        paper.save()

        try:
            from apps.reviews.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action="SOLUTION_UPLOADED",
                target_type="AcademicPaper",
                target_id=str(paper.id),
                details=f"Uploaded solution for {paper.subject.code} ({paper.exam_session} {paper.exam_year})",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Solution for {paper.subject.code} ({paper.exam_session} {paper.exam_year}) was successfully uploaded and is now available for students."
        )
        return redirect("papers:detail", pk=pk)

    return redirect("papers:detail", pk=pk)


@login_required
def delete_solution(request, pk):
    """Administrator removal of PYQ solution, reverting status to Coming Soon."""
    paper = get_object_or_404(AcademicPaper, pk=pk)

    is_authorized = (
        request.user.is_superuser
        or request.user.is_staff
        or getattr(request.user, "is_administrator", False)
    )
    if not is_authorized:
        return HttpResponseForbidden("Only administrators can remove paper solutions.")

    if request.method == "POST":
        paper.solution_file = None
        paper.solution_file_size = 0
        paper.solution_uploaded_at = None
        paper.solution_uploaded_by = None
        paper.save()

        try:
            from apps.reviews.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action="SOLUTION_DELETED",
                target_type="AcademicPaper",
                target_id=str(paper.id),
                details=f"Removed solution for {paper.subject.code} ({paper.exam_session} {paper.exam_year})",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception:
            pass

        messages.info(request, f"Solution for {paper.subject.code} has been removed. Status is now set to Coming Soon.")
        return redirect("papers:detail", pk=pk)

    return redirect("papers:detail", pk=pk)
