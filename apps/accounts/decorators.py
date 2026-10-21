from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login

def student_required(view_func):
    """Ensure the user is authenticated."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to access your student workspace.")
            return redirect_to_login(request.get_full_path(), login_url="accounts:login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def reviewer_required(view_func):
    """Ensure the user has reviewer or administrator role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to access reviewer tools.")
            return redirect_to_login(request.get_full_path(), login_url="accounts:login")
        if not (request.user.is_reviewer or request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("You do not have reviewer permissions to view this resource.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    """Ensure the user has administrator privileges."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to access administration.")
            return redirect_to_login(request.get_full_path(), login_url="accounts:login")
        if not (request.user.is_administrator or request.user.is_superuser):
            raise PermissionDenied("Administrator privileges are required to view this resource.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
