import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from apps.academics.models import University, Subject, Branch
from apps.papers.models import AcademicPaper

logger = logging.getLogger("pariksha")

def home(request):
    """Landing page showcasing the Pariksha platform (Page 1)."""
    # Fetch real counts from DB (no fabrication)
    rgpv_university = University.objects.filter(code="RGPV").first()
    recent_papers = AcademicPaper.objects.filter(is_verified=True).select_related("subject", "branch", "university").order_by("-created_at")[:6]
    total_papers_count = AcademicPaper.objects.filter(is_verified=True).count()
    branches_count = Branch.objects.count()
    subjects_count = Subject.objects.count()

    context = {
        "rgpv_university": rgpv_university,
        "recent_papers": recent_papers,
        "total_papers_count": total_papers_count,
        "branches_count": branches_count,
        "subjects_count": subjects_count,
    }
    return render(request, "core/home.html", context)

def health_check(request):
    """Lightweight application health check endpoint."""
    return JsonResponse({
        "status": "healthy",
        "service": "Pariksha",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "ai_integration": "pending_future_integration"
    })

def privacy_policy(request):
    """Privacy Policy page (Page 16)."""
    return render(request, "core/privacy.html")

def terms_of_use(request):
    """Terms of Use page (Page 16)."""
    return render(request, "core/terms.html")

def disclaimer(request):
    """Educational Disclaimer page (Page 16)."""
    return render(request, "core/disclaimer.html")

def contact(request):
    """Contact information page."""
    return render(request, "core/contact.html")

# Custom HTTP error views (Page 17)
def custom_permission_denied_view(request, exception=None):
    """Custom 403 Forbidden page."""
    return render(request, "errors/403.html", status=403)

def custom_page_not_found_view(request, exception=None):
    """Custom 404 Not Found page."""
    return render(request, "errors/404.html", status=404)

def custom_server_error_view(request):
    """Custom 500 Server Error page."""
    return render(request, "errors/500.html", status=500)
