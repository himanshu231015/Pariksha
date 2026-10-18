import os
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.utils import timezone
from .models import SyllabusDocument
from .forms import SyllabusUploadForm
from apps.accounts.decorators import admin_required
from apps.reviews.models import AuditLog

def syllabus_list(request):
    """List official syllabus documents. Students see published; Admins see all (Page 15)."""
    is_admin = request.user.is_authenticated and (request.user.is_administrator or request.user.is_superuser)

    qs = SyllabusDocument.objects.select_related("university", "program", "branch", "semester", "subject")
    if not is_admin:
        qs = qs.filter(is_published=True)

    branch_id = request.GET.get("branch")
    semester_id = request.GET.get("semester")

    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    if semester_id:
        qs = qs.filter(semester_id=semester_id)

    context = {
        "syllabi": qs,
        "is_admin": is_admin,
    }
    return render(request, "syllabus/list.html", context)


@admin_required
def syllabus_upload(request):
    """Administrator-only upload workflow for official syllabus documents (Page 15)."""
    if request.method == "POST":
        form = SyllabusUploadForm(request.POST, request.FILES)
        if form.is_valid():
            syllabus = form.save(commit=False)
            syllabus.uploaded_by = request.user
            uploaded_file = request.FILES.get("file")
            syllabus.file_size = uploaded_file.size
            if syllabus.is_published:
                syllabus.published_at = timezone.now()
            syllabus.save()

            AuditLog.objects.create(
                user=request.user,
                action="SYLLABUS_DOCUMENT_UPLOADED",
                target_type="SyllabusDocument",
                target_id=str(syllabus.id),
                details=f"Uploaded syllabus for {syllabus.subject.code} ({syllabus.academic_year} {syllabus.version})",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            messages.success(request, f"Official syllabus for {syllabus.subject.code} uploaded successfully.")
            return redirect("syllabus:list")
        else:
            messages.error(request, "Syllabus upload failed. Please correct the form errors.")
    else:
        form = SyllabusUploadForm()

    return render(request, "syllabus/upload.html", {"form": form})


@admin_required
def syllabus_toggle_publish(request, pk):
    """Toggle publish/unpublish status of a syllabus document."""
    syllabus = get_object_or_404(SyllabusDocument, pk=pk)
    syllabus.is_published = not syllabus.is_published
    if syllabus.is_published:
        syllabus.published_at = timezone.now()
    syllabus.save(update_fields=["is_published", "published_at"])

    status_str = "Published" if syllabus.is_published else "Unpublished (Draft)"
    AuditLog.objects.create(
        user=request.user,
        action=f"SYLLABUS_{status_str.upper()}",
        target_type="SyllabusDocument",
        target_id=str(syllabus.id),
        details=f"Changed publication status to {status_str}",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    messages.info(request, f"Syllabus #{syllabus.id} status changed to {status_str}.")
    return redirect("syllabus:list")


@login_required
def syllabus_download(request, pk):
    """Download official syllabus document."""
    syllabus = get_object_or_404(SyllabusDocument, pk=pk)

    # Permission check: Non-admins cannot download unpublished drafts
    is_admin = request.user.is_administrator or request.user.is_superuser
    if not syllabus.is_published and not is_admin:
        raise PermissionDenied("This syllabus is not published yet.")

    if not syllabus.file or not os.path.exists(syllabus.file.path):
        raise Http404("Syllabus document file not found on disk.")

    content_type, _ = mimetypes.guess_type(syllabus.file.path)
    safe_name = f"Syllabus_{syllabus.subject.code}_{syllabus.academic_year}.pdf"

    response = FileResponse(open(syllabus.file.path, "rb"), content_type=content_type or "application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return response


@login_required
def syllabus_preview(request, pk):
    """Safe inline preview of syllabus PDF."""
    syllabus = get_object_or_404(SyllabusDocument, pk=pk)

    is_admin = request.user.is_administrator or request.user.is_superuser
    if not syllabus.is_published and not is_admin:
        raise PermissionDenied("This syllabus document is not published yet.")

    if not syllabus.file or not os.path.exists(syllabus.file.path):
        raise Http404("Document not found.")

    response = FileResponse(open(syllabus.file.path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = "inline"
    return response
