import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution
from apps.academics.models import University, Program, Branch, Semester, Subject, SyllabusUnit
from .forms import AskParikshaForm, PredictedPaperConfigForm, MustPrepareFilterForm
from .services import AssistantService
from .schemas import AssistantInquiryRequest, AssistantInquiryResponse


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
    # Check if user requested a reset
    if request.GET.get("reset") == "1":
        request.session.pop("assistant_chat_history", None)
        request.session.pop("applied_academic_context", None)
        return redirect("assistant_ui:chat")

    applied_context = request.session.get("applied_academic_context", {})
    chat_history = request.session.get("assistant_chat_history", [])

    # Pre-populate form: session context takes priority, then student profile
    initial_data = {}
    if applied_context:
        initial_data = {
            "university": applied_context.get("university_id"),
            "program": applied_context.get("program_id"),
            "branch": applied_context.get("branch_id"),
            "semester": applied_context.get("semester_id"),
            "subject": applied_context.get("subject_id"),
            "requested_format": applied_context.get("requested_format", "detailed"),
            "workflow_intent": applied_context.get("workflow_intent", "exam_prep"),
        }
    elif request.user.is_authenticated:
        profile = getattr(request.user, "student_profile", None)
        if profile:
            initial_data = {
                "university": profile.university_id,
                "program": profile.program_id,
                "branch": profile.branch_id,
                "semester": profile.semester_id,
                "requested_format": profile.preferred_answer_format,
            }

    form = AskParikshaForm(request.POST or None, initial=initial_data if not request.POST else None)

    # Handle standard non-AJAX POST submissions
    if request.method == "POST" and form.is_valid():
        action = request.POST.get("action", "send_message")

        # Action: Apply Academic Context
        if action == "apply_context":
            context_data = _save_context_to_session(request, form.cleaned_data)
            greeting_msg = _build_context_applied_greeting(context_data)
            chat_history.append({
                "type": "assistant",
                "badge": "Academic Context Active",
                "badge_class": "bg-success",
                "text": greeting_msg,
                "is_context_banner": True,
                "context_summary": context_data,
            })
            request.session["assistant_chat_history"] = chat_history
            return redirect("assistant_ui:chat")

        # Action: Send Question Message
        user_query = form.cleaned_data.get("message")
        if user_query:
            inquiry_request = AssistantInquiryRequest(
                message=user_query,
                university_id=form.cleaned_data["university"].id if form.cleaned_data.get("university") else None,
                course_id=form.cleaned_data["program"].id if form.cleaned_data.get("program") else None,
                branch_id=form.cleaned_data["branch"].id if form.cleaned_data.get("branch") else None,
                semester_id=form.cleaned_data["semester"].id if form.cleaned_data.get("semester") else None,
                subject_id=form.cleaned_data["subject"].id if form.cleaned_data.get("subject") else None,
                requested_format=form.cleaned_data.get("requested_format", "detailed"),
                workflow_intent=form.cleaned_data.get("workflow_intent", "exam_prep"),
            )
            response_data = AssistantService.send_inquiry(inquiry_request)

            # Append to session chat history
            chat_history.append({
                "type": "user",
                "text": user_query,
            })
            chat_history.append({
                "type": "assistant",
                "status": response_data.status,
                "search_strategy": response_data.search_strategy,
                "text": response_data.answer_text,
                "paper_title": response_data.paper_title,
                "paper_code": response_data.paper_code,
                "exam_year": response_data.exam_year,
                "exam_session": response_data.exam_session,
                "pyq_solution_url": response_data.pyq_solution_url,
                "pyq_preview_url": response_data.pyq_preview_url,
                "grounded_unit": response_data.grounded_unit,
                "limitations_disclaimer": response_data.limitations_disclaimer,
                "sources": [
                    {
                        "title": s.title,
                        "document_type": s.document_type,
                        "year": s.year,
                        "session": s.session,
                        "download_url": s.download_url,
                    }
                    for s in response_data.sources
                ],
            })
            request.session["assistant_chat_history"] = chat_history
            return redirect("assistant_ui:chat")

    # Determine active subject for dynamic suggested questions
    active_subject_id = None
    if applied_context.get("subject_id"):
        active_subject_id = applied_context["subject_id"]
    elif form.is_bound and form.cleaned_data.get("subject"):
        active_subject_id = form.cleaned_data["subject"].id
    elif initial_data.get("subject"):
        active_subject_id = initial_data["subject"]

    suggested_questions = AssistantService.get_suggested_questions(
        active_subject_id,
        intent=applied_context.get("workflow_intent", "exam_prep")
    )

    context = {
        "form": form,
        "chat_history": chat_history,
        "applied_context": applied_context,
        "suggested_questions": suggested_questions,
        "is_ai_connected": AssistantService.is_ai_backend_configured(),
    }
    return render(request, "assistant/chat.html", context)


@login_required
@require_POST
def api_apply_context(request):
    """AJAX endpoint: Apply chosen academic context and return personalized questions."""
    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    except Exception:
        data = request.POST

    university_id = data.get("university") or None
    program_id = data.get("program") or None
    branch_id = data.get("branch") or None
    semester_id = data.get("semester") or None
    subject_id = data.get("subject") or None
    workflow_intent = data.get("workflow_intent", "exam_prep")
    requested_format = data.get("requested_format", "detailed")

    # Fetch readable names
    uni = University.objects.filter(id=university_id).first() if university_id else None
    prog = Program.objects.filter(id=program_id).first() if program_id else None
    br = Branch.objects.filter(id=branch_id).first() if branch_id else None
    sem = Semester.objects.filter(id=semester_id).first() if semester_id else None
    subj = Subject.objects.filter(id=subject_id).first() if subject_id else None

    context_data = {
        "university_id": int(university_id) if university_id else None,
        "university_name": uni.short_name if uni else "RGPV Bhopal",
        "program_id": int(program_id) if program_id else None,
        "program_name": prog.code if prog else "B.Tech",
        "branch_id": int(branch_id) if branch_id else None,
        "branch_name": f"{br.name} ({br.code})" if br else "General Engineering",
        "semester_id": int(semester_id) if semester_id else None,
        "semester_title": sem.title if sem else "All Semesters",
        "subject_id": int(subject_id) if subject_id else None,
        "subject_code": subj.code if subj else "",
        "subject_name": subj.name if subj else "",
        "workflow_intent": workflow_intent,
        "requested_format": requested_format,
    }

    # Save to session
    request.session["applied_academic_context"] = context_data

    # Generate assistant greeting message
    greeting_msg = _build_context_applied_greeting(context_data)

    chat_history = request.session.get("assistant_chat_history", [])
    chat_history.append({
        "type": "assistant",
        "badge": "Academic Context Active",
        "badge_class": "bg-success",
        "text": greeting_msg,
        "is_context_banner": True,
        "context_summary": context_data,
    })
    request.session["assistant_chat_history"] = chat_history

    # Dynamic suggestions tailored to this subject
    suggested_questions = AssistantService.get_suggested_questions(
        context_data["subject_id"], intent=workflow_intent
    )

    return JsonResponse({
        "status": "success",
        "message": "Academic context applied successfully.",
        "context": context_data,
        "greeting_msg": greeting_msg,
        "suggested_questions": suggested_questions,
    })


@login_required
@require_POST
def api_ask_question(request):
    """
    AJAX endpoint: Processes question by searching verified PYQ solutions first,
    falling back to the Academic Tool Call if no uploaded solution exists.
    """
    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    except Exception:
        data = request.POST

    user_query = data.get("message", "").strip()
    if not user_query:
        return HttpResponseBadRequest("A query message is required.")

    # Read active context from request data or session
    session_ctx = request.session.get("applied_academic_context", {})
    university_id = data.get("university") or session_ctx.get("university_id")
    program_id = data.get("program") or session_ctx.get("program_id")
    branch_id = data.get("branch") or session_ctx.get("branch_id")
    semester_id = data.get("semester") or session_ctx.get("semester_id")
    subject_id = data.get("subject") or session_ctx.get("subject_id")
    requested_format = data.get("requested_format") or session_ctx.get("requested_format", "detailed")
    workflow_intent = data.get("workflow_intent") or session_ctx.get("workflow_intent", "exam_prep")

    inquiry = AssistantInquiryRequest(
        message=user_query,
        university_id=int(university_id) if university_id else None,
        course_id=int(program_id) if program_id else None,
        branch_id=int(branch_id) if branch_id else None,
        semester_id=int(semester_id) if semester_id else None,
        subject_id=int(subject_id) if subject_id else None,
        requested_format=requested_format,
        workflow_intent=workflow_intent,
    )

    response_data = AssistantService.send_inquiry(inquiry)

    # Append to session chat history
    chat_history = request.session.get("assistant_chat_history", [])
    chat_history.append({
        "type": "user",
        "text": user_query,
    })
    chat_history.append({
        "type": "assistant",
        "status": response_data.status,
        "search_strategy": response_data.search_strategy,
        "text": response_data.answer_text,
        "paper_title": response_data.paper_title,
        "paper_code": response_data.paper_code,
        "exam_year": response_data.exam_year,
        "exam_session": response_data.exam_session,
        "pyq_solution_url": response_data.pyq_solution_url,
        "pyq_preview_url": response_data.pyq_preview_url,
        "grounded_unit": response_data.grounded_unit,
        "limitations_disclaimer": response_data.limitations_disclaimer,
        "sources": [
            {
                "title": s.title,
                "document_type": s.document_type,
                "year": s.year,
                "session": s.session,
                "download_url": s.download_url,
            }
            for s in response_data.sources
        ],
    })
    request.session["assistant_chat_history"] = chat_history

    return JsonResponse({
        "status": "success",
        "user_query": user_query,
        "response": {
            "status": response_data.status,
            "search_strategy": response_data.search_strategy,
            "answer_text": response_data.answer_text,
            "paper_title": response_data.paper_title,
            "paper_code": response_data.paper_code,
            "exam_year": response_data.exam_year,
            "exam_session": response_data.exam_session,
            "pyq_solution_url": response_data.pyq_solution_url,
            "pyq_preview_url": response_data.pyq_preview_url,
            "grounded_unit": response_data.grounded_unit,
            "limitations_disclaimer": response_data.limitations_disclaimer,
            "sources": [
                {
                    "title": s.title,
                    "document_type": s.document_type,
                    "year": s.year,
                    "session": s.session,
                    "download_url": s.download_url,
                }
                for s in response_data.sources
            ],
        },
    })


def _save_context_to_session(request, cleaned_data) -> dict:
    """Helper to convert form cleaned_data into session dict."""
    uni = cleaned_data.get("university")
    prog = cleaned_data.get("program")
    br = cleaned_data.get("branch")
    sem = cleaned_data.get("semester")
    subj = cleaned_data.get("subject")

    context_data = {
        "university_id": uni.id if uni else None,
        "university_name": uni.short_name if uni else "RGPV Bhopal",
        "program_id": prog.id if prog else None,
        "program_name": prog.code if prog else "B.Tech",
        "branch_id": br.id if br else None,
        "branch_name": f"{br.name} ({br.code})" if br else "General Engineering",
        "semester_id": sem.id if sem else None,
        "semester_title": sem.title if sem else "All Semesters",
        "subject_id": subj.id if subj else None,
        "subject_code": subj.code if subj else "",
        "subject_name": subj.name if subj else "",
        "workflow_intent": cleaned_data.get("workflow_intent", "exam_prep"),
        "requested_format": cleaned_data.get("requested_format", "detailed"),
    }
    request.session["applied_academic_context"] = context_data
    return context_data


def _build_context_applied_greeting(ctx: dict) -> str:
    """Create friendly assistant greeting detailing applied context."""
    subj_label = f"{ctx['subject_code']} - {ctx['subject_name']}" if ctx.get("subject_code") else "General Engineering"
    fmt_display = {
        "detailed": "Detailed Exam Steps & Diagrams",
        "concise": "Concise Bullet Points & Summaries",
        "formula_first": "Formulas & Mathematical Derivations First",
    }.get(ctx.get("requested_format"), "Detailed Exam Steps & Diagrams")

    intent_display = {
        "exam_prep": "Exam-Oriented Concept Preparation",
        "find_pyqs": "Locate Relevant PYQ Questions",
        "answer_gen": "Format Model 7-Mark Answer",
        "must_prepare": "Highlight Crucial Topic Weightage",
        "general": "General Academic Inquiry",
    }.get(ctx.get("workflow_intent"), "Exam Preparation")

    return (
        f"**Academic Context Applied Successfully!**\n\n"
        f"- **Subject:** {subj_label}\n"
        f"- **Branch & Semester:** {ctx['branch_name']} | {ctx['semester_title']}\n"
        f"- **Workflow Intent:** {intent_display}\n"
        f"- **Answer Format:** {fmt_display}\n\n"
        f"Pariksha Assistant is now configured. When you submit a question:\n"
        f"1. I will search verified **PYQ solutions** in the repository first.\n"
        f"2. If no exact PYQ solution is available, I will invoke the **Academic Tool Call** to generate an exam-ready answer according to this syllabus context.\n\n"
        f"Ask your question below or pick a suggested question!"
    )


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
