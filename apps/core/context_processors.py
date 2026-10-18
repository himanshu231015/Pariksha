from django.conf import settings
from datetime import datetime

def platform_context(request):
    """Platform-wide context variables available in all templates."""
    google_configured = bool(getattr(settings, "GOOGLE_CLIENT_ID", "").strip())
    
    # Check user role if authenticated
    is_reviewer = False
    is_administrator = False
    student_profile = None
    
    if request.user.is_authenticated:
        is_reviewer = getattr(request.user, "is_reviewer", False) or request.user.is_staff or request.user.is_superuser
        is_administrator = getattr(request.user, "is_administrator", False) or request.user.is_superuser
        if hasattr(request.user, "student_profile"):
            student_profile = request.user.student_profile

    return {
        "PLATFORM_NAME": "Pariksha",
        "PLATFORM_TAGLINE": "RGPV Exam Preparation & Academic Intelligence Platform",
        "CURRENT_YEAR": datetime.now().year,
        "GOOGLE_OAUTH_CONFIGURED": google_configured,
        "AI_INTEGRATION_CONFIGURED": False,  # Non-AI phase: explicitly flagged as awaiting integration
        "IS_REVIEWER_USER": is_reviewer,
        "IS_ADMIN_USER": is_administrator,
        "USER_STUDENT_PROFILE": student_profile,
    }
