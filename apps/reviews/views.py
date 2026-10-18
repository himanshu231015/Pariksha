import os
import shutil
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.core.paginator import Paginator
from django.conf import settings
from .models import PaperContribution, ReviewDecision, AuditLog
from .forms import PaperContributionForm, ReviewActionForm
from apps.accounts.decorators import student_required, reviewer_required, admin_required
from apps.papers.models import AcademicPaper
from apps.academics.models import University, Program, Branch, Semester, Subject
from apps.syllabus.models import SyllabusDocument
from django.contrib.auth import get_user_model

User = get_user_model()

@student_required
def contribute_paper(request):
    """Student submission workflow for question papers (Page 9)."""
    if request.method == "POST":
        form = PaperContributionForm(request.POST, request.FILES)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.contributor = request.user
            uploaded_file = request.FILES.get("file")
            contribution.original_filename = uploaded_file.name
            contribution.file_size = uploaded_file.size
            contribution.file_type = uploaded_file.content_type or "application/octet-stream"
            contribution.paper_title = (
                f"{contribution.subject.code} {contribution.exam_session} {contribution.exam_year}"
            )
            contribution.status = PaperContribution.STATUS_PENDING
            contribution.save()

            AuditLog.objects.create(
                user=request.user,
                action="CONTRIBUTION_SUBMITTED",
                target_type="PaperContribution",
                target_id=str(contribution.id),
                details=f"Submitted paper for {contribution.subject.code} ({contribution.exam_session} {contribution.exam_year})",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            messages.success(
                request,
                f"Thank you! Your paper for {contribution.subject.code} ({contribution.exam_session} {contribution.exam_year}) has been submitted for peer review."
            )
            return redirect("reviews:my_contributions")
        else:
            messages.error(request, "Submission could not be completed. Please correct the highlighted errors.")
    else:
        # Prepopulate with student's profile preferences if available
        initial_data = {}
        profile = getattr(request.user, "student_profile", None)
        if profile:
            if profile.university:
                initial_data["university"] = profile.university
            if profile.program:
                initial_data["program"] = profile.program
            if profile.branch:
                initial_data["branch"] = profile.branch
            if profile.semester:
                initial_data["semester"] = profile.semester
        form = PaperContributionForm(initial=initial_data)

    return render(request, "contributions/submit.html", {"form": form})


@student_required
def my_contributions(request):
    """View submissions belonging exclusively to the authenticated student (Page 10)."""
    contributions = (
        PaperContribution.objects.filter(contributor=request.user)
        .select_related("university", "program", "branch", "semester", "subject")
        .prefetch_related("review_history")
        .order_by("-created_at")
    )

    paginator = Paginator(contributions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "contributions/my_list.html", {"page_obj": page_obj})


@login_required
def contribution_file_download(request, pk):
    """Secure access to uploaded paper files (author or reviewer/admin only)."""
    contribution = get_object_or_404(PaperContribution, pk=pk)

    # Permission check: Only the student author or an authorized reviewer/admin can download
    is_author = contribution.contributor == request.user
    is_staff_reviewer = request.user.is_reviewer or request.user.is_staff or request.user.is_superuser

    if not (is_author or is_staff_reviewer):
        raise PermissionDenied("You do not have permission to access this private document.")

    if not contribution.file or not os.path.exists(contribution.file.path):
        raise Http404("Contribution document file not found on disk.")

    content_type, _ = mimetypes.guess_type(contribution.file.path)
    response = FileResponse(open(contribution.file.path, "rb"), content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'inline; filename="{contribution.original_filename}"'
    return response


@reviewer_required
def reviewer_dashboard(request):
    """Internal review dashboard for authorized reviewers (Page 12)."""
    status_filter = request.GET.get("status", "all")
    subject_filter = request.GET.get("subject")
    year_filter = request.GET.get("year")

    contributions_qs = PaperContribution.objects.select_related(
        "contributor", "university", "program", "branch", "semester", "subject"
    ).order_by("-created_at")

    if status_filter != "all" and status_filter in dict(PaperContribution.STATUS_CHOICES):
        contributions_qs = contributions_qs.filter(status=status_filter)

    if subject_filter:
        contributions_qs = contributions_qs.filter(subject_id=subject_filter)

    if year_filter:
        contributions_qs = contributions_qs.filter(exam_year=year_filter)

    # Status counts for dashboard metrics
    counts = {
        "pending": PaperContribution.objects.filter(status=PaperContribution.STATUS_PENDING).count(),
        "processing": PaperContribution.objects.filter(status=PaperContribution.STATUS_PROCESSING).count(),
        "approved": PaperContribution.objects.filter(status=PaperContribution.STATUS_APPROVED).count(),
        "rejected": PaperContribution.objects.filter(status=PaperContribution.STATUS_REJECTED).count(),
        "needs_correction": PaperContribution.objects.filter(status=PaperContribution.STATUS_NEEDS_CORRECTION).count(),
        "duplicate": PaperContribution.objects.filter(status=PaperContribution.STATUS_DUPLICATE).count(),
        "total": PaperContribution.objects.count(),
    }

    paginator = Paginator(contributions_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "counts": counts,
        "current_status": status_filter,
        "subjects": Subject.objects.filter(is_active=True),
        "selected_subject": str(subject_filter) if subject_filter else "",
        "selected_year": str(year_filter) if year_filter else "",
    }
    return render(request, "reviews/dashboard.html", context)


@reviewer_required
def review_detail(request, pk):
    """Document review, metadata correction, and decision workflow (Page 13)."""
    contribution = get_object_or_404(
        PaperContribution.objects.select_related(
            "contributor", "university", "program", "branch", "semester", "subject"
        ),
        pk=pk,
    )

    # Anti self-review security rule: A student must never approve or review their own submission
    if contribution.contributor == request.user and not request.user.is_superuser:
        messages.error(request, "Security policy violation: You cannot review or approve your own paper submission.")
        return redirect("reviews:dashboard")

    # Check for potential duplicates in catalog
    matching_approved = AcademicPaper.objects.filter(
        university=contribution.university,
        program=contribution.program,
        branch=contribution.branch,
        semester=contribution.semester,
        subject=contribution.subject,
        exam_year=contribution.exam_year,
        exam_session=contribution.exam_session,
        is_verified=True,
    ).first()

    if request.method == "POST":
        form = ReviewActionForm(request.POST, instance=contribution)
        if form.is_valid():
            with transaction.atomic():
                updated_contribution = form.save()
                decision = form.cleaned_data["decision"]
                feedback = form.cleaned_data.get("feedback_to_student", "").strip()
                internal_notes = form.cleaned_data.get("internal_notes", "").strip()

                # Record decision
                ReviewDecision.objects.create(
                    contribution=updated_contribution,
                    reviewer=request.user,
                    decision=decision,
                    feedback_to_student=feedback,
                    internal_notes=internal_notes,
                )

                if decision == ReviewDecision.DECISION_APPROVED:
                    updated_contribution.status = PaperContribution.STATUS_APPROVED
                    updated_contribution.save(update_fields=["status"])

                    # Create or update verified AcademicPaper
                    # Determine safe file copy for verified repository
                    new_paper, created = AcademicPaper.objects.get_or_create(
                        university=updated_contribution.university,
                        program=updated_contribution.program,
                        branch=updated_contribution.branch,
                        semester=updated_contribution.semester,
                        subject=updated_contribution.subject,
                        exam_year=updated_contribution.exam_year,
                        exam_session=updated_contribution.exam_session,
                        defaults={
                            "paper_title": f"{updated_contribution.subject.code} {updated_contribution.exam_session} {updated_contribution.exam_year}",
                            "file": updated_contribution.file,
                            "file_size": updated_contribution.file_size,
                            "file_type": updated_contribution.file_type,
                            "is_verified": True,
                            "contributor": updated_contribution.contributor,
                            "verified_by": request.user,
                        },
                    )
                    if not created:
                        new_paper.file = updated_contribution.file
                        new_paper.verified_by = request.user
                        new_paper.is_verified = True
                        new_paper.save()

                    AuditLog.objects.create(
                        user=request.user,
                        action="PAPER_APPROVED_AND_PUBLISHED",
                        target_type="AcademicPaper",
                        target_id=str(new_paper.id),
                        details=f"Approved contribution #{updated_contribution.id} for {updated_contribution.subject.code}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                    messages.success(request, f"Contribution #{updated_contribution.id} approved and published to PYQ Catalog as Paper #{new_paper.id}.")

                elif decision == ReviewDecision.DECISION_REJECTED:
                    updated_contribution.status = PaperContribution.STATUS_REJECTED
                    updated_contribution.save(update_fields=["status"])
                    AuditLog.objects.create(
                        user=request.user,
                        action="PAPER_REJECTED",
                        target_type="PaperContribution",
                        target_id=str(updated_contribution.id),
                        details=f"Rejected: {feedback}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                    messages.warning(request, f"Contribution #{updated_contribution.id} has been marked Rejected.")

                elif decision == ReviewDecision.DECISION_NEEDS_CORRECTION:
                    updated_contribution.status = PaperContribution.STATUS_NEEDS_CORRECTION
                    updated_contribution.save(update_fields=["status"])
                    AuditLog.objects.create(
                        user=request.user,
                        action="PAPER_CORRECTION_REQUESTED",
                        target_type="PaperContribution",
                        target_id=str(updated_contribution.id),
                        details=f"Corrections requested: {feedback}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                    messages.info(request, f"Contribution #{updated_contribution.id} marked as Needs Correction.")

                elif decision == ReviewDecision.DECISION_DUPLICATE:
                    updated_contribution.status = PaperContribution.STATUS_DUPLICATE
                    updated_contribution.save(update_fields=["status"])
                    AuditLog.objects.create(
                        user=request.user,
                        action="PAPER_MARKED_DUPLICATE",
                        target_type="PaperContribution",
                        target_id=str(updated_contribution.id),
                        details=f"Marked as duplicate. Notes: {internal_notes}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                    messages.info(request, f"Contribution #{updated_contribution.id} marked as Duplicate.")

                return redirect("reviews:dashboard")
        else:
            messages.error(request, "Please review the form errors before saving.")
    else:
        form = ReviewActionForm(instance=contribution, initial={"decision": ReviewDecision.DECISION_APPROVED})

    review_history = contribution.review_history.select_related("reviewer").all()

    context = {
        "contribution": contribution,
        "form": form,
        "matching_approved": matching_approved,
        "review_history": review_history,
    }
    return render(request, "reviews/detail.html", context)


@admin_required
def admin_dashboard(request):
    """Custom Administrator Dashboard (Page 14)."""
    stats = {
        "users_count": User.objects.count(),
        "students_count": User.objects.filter(role=User.ROLE_STUDENT).count(),
        "reviewers_count": User.objects.filter(role=User.ROLE_REVIEWER).count(),
        "verified_papers_count": AcademicPaper.objects.filter(is_verified=True).count(),
        "pending_reviews_count": PaperContribution.objects.filter(status=PaperContribution.STATUS_PENDING).count(),
        "syllabus_count": SyllabusDocument.objects.count(),
        "subjects_count": Subject.objects.count(),
        "branches_count": Branch.objects.count(),
    }

    recent_logs = AuditLog.objects.select_related("user").order_by("-timestamp")[:10]
    recent_contributions = PaperContribution.objects.select_related("contributor", "subject").order_by("-created_at")[:5]

    context = {
        "stats": stats,
        "recent_logs": recent_logs,
        "recent_contributions": recent_contributions,
    }
    return render(request, "reviews/admin_dashboard.html", context)


@admin_required
def admin_audit_logs(request):
    """View system audit logs."""
    logs_qs = AuditLog.objects.select_related("user").order_by("-timestamp")
    action_filter = request.GET.get("action")
    if action_filter:
        logs_qs = logs_qs.filter(action__icontains=action_filter)

    paginator = Paginator(logs_qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "reviews/audit_logs.html", {"page_obj": page_obj})
