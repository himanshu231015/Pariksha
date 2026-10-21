from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution
from apps.academics.models import University, Program, Branch, Semester, Subject, SyllabusUnit
from .forms import AskParikshaForm, PredictedPaperConfigForm, MustPrepareFilterForm
from .services import AssistantService
from .schemas import AssistantInquiryRequest

@login_required
def dashboard_view(request):
    """Student Dashboard prioritizing the 3 core actions (Page 3)."""
    profile = getattr(request.user, "student_profile", None)

    # Real data queries
    recent_contributions = (
        PaperContribution.objects.filter(contributor=request.user)
        .select_related("subject", "branch")
        .order_by("-created_at")[:4]
    )

    # Real verified papers relevant to student's branch/semester if profile is configured
    suggested_papers = []
    if profile and profile.branch and profile.semester:
        suggested_papers = (
            AcademicPaper.objects.filter(
                branch=profile.branch,
                semester=profile.semester,
                is_verified=True,
            )
            .select_related("subject", "university")
            .order_by("-exam_year")[:5]
        )
    elif not profile or not profile.is_complete:
        # Fallback to general recent verified papers if profile incomplete
        suggested_papers = (
            AcademicPaper.objects.filter(is_verified=True)
            .select_related("subject", "university", "branch")
            .order_by("-created_at")[:5]
        )

    context = {
        "profile": profile,
        "recent_contributions": recent_contributions,
        "suggested_papers": suggested_papers,
        "total_contributions": request.user.contributions.count(),
        "is_profile_complete": profile.is_complete if profile else False,
    }
    return render(request, "dashboard/index.html", context)


@login_required
def assistant_chat_view(request):
    """Ask Pariksha Chat-Style Interface (Page 4)."""
    form = AskParikshaForm(request.POST or None)

    # Pre-populate with student academic defaults if available
    if not request.POST and request.user.is_authenticated:
        profile = getattr(request.user, "student_profile", None)
        if profile:
            form = AskParikshaForm(
                initial={
                    "university": profile.university,
                    "program": profile.program,
                    "branch": profile.branch,
                    "semester": profile.semester,
                    "requested_format": profile.preferred_answer_format,
                }
            )

    response_data = None
    user_query = None

    if request.method == "POST" and form.is_valid():
        user_query = form.cleaned_data["message"]
        inquiry_request = AssistantInquiryRequest(
            message=user_query,
            university_id=form.cleaned_data["university"].id if form.cleaned_data.get("university") else None,
            course_id=form.cleaned_data["program"].id if form.cleaned_data.get("program") else None,
            branch_id=form.cleaned_data["branch"].id if form.cleaned_data.get("branch") else None,
            semester_id=form.cleaned_data["semester"].id if form.cleaned_data.get("semester") else None,
            subject_id=form.cleaned_data["subject"].id if form.cleaned_data.get("subject") else None,
            requested_format=form.cleaned_data["requested_format"],
            workflow_intent=form.cleaned_data["workflow_intent"],
        )
        # Pass to service boundary (returns honest pending integration state)
        response_data = AssistantService.send_inquiry(inquiry_request)

    suggested_questions = [
        "Explain Round Robin Scheduling with a time quantum of 2ms and draw the Gantt chart.",
        "What are the differences between Paging and Segmentation in Memory Management?",
        "Derive the time complexity of Quick Sort in best, average, and worst cases.",
        "Explain the working of Bellman-Ford shortest path algorithm with an example.",
        "What is 3NF and BCNF normalization in Database Management Systems?",
    ]

    context = {
        "form": form,
        "response_data": response_data,
        "user_query": user_query,
        "suggested_questions": suggested_questions,
        "is_ai_connected": AssistantService.is_ai_backend_configured(),
    }
    return render(request, "assistant/chat.html", context)


@login_required
def must_prepare_view(request):
    """Subject-specific preparation priorities and unit breakdown (Page 7)."""
    form = MustPrepareFilterForm(request.GET or None)

    selected_subject = None
    syllabus_units = []
    verified_papers_count = 0

    if form.is_valid() and form.cleaned_data.get("subject"):
        selected_subject = form.cleaned_data["subject"]
        syllabus_units = SyllabusUnit.objects.filter(subject=selected_subject).order_by("unit_number")
        verified_papers_count = AcademicPaper.objects.filter(subject=selected_subject, is_verified=True).count()

    context = {
        "form": form,
        "selected_subject": selected_subject,
        "syllabus_units": syllabus_units,
        "verified_papers_count": verified_papers_count,
        "is_ai_connected": AssistantService.is_ai_backend_configured(),
    }
    return render(request, "preparation/must_prepare.html", context)


@login_required
def predicted_paper_view(request):
    """Predicted Practice Paper Configuration & Layout (Page 8)."""
    form = PredictedPaperConfigForm(request.GET or None)

    selected_subject = None
    units = []

    if form.is_valid():
        selected_subject = form.cleaned_data["subject"]
        units = SyllabusUnit.objects.filter(subject=selected_subject).order_by("unit_number")

    context = {
        "form": form,
        "selected_subject": selected_subject,
        "units": units,
        "is_ai_connected": AssistantService.is_ai_backend_configured(),
    }
    return render(request, "preparation/predicted_paper.html", context)
