from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, StudentProfileForm
from .models import StudentProfile

def login_view(request):
    """Sign-in page supporting both Google OAuth and standard credentials (Page 2)."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get("next") or "dashboard:index"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def signup_view(request):
    """Student registration page."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Account created successfully! Please configure your academic profile.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


def logout_view(request):
    """Log out current user securely."""
    logout(request)
    messages.info(request, "You have been logged out of Pariksha.")
    return redirect("core:home")


@login_required
def profile_view(request):
    """Student profile and academic settings management (Page 11)."""
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your academic profile preferences have been updated.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Please resolve the academic catalog errors below.")
    else:
        form = StudentProfileForm(instance=profile, user=request.user)

    # Real contribution counts for this user
    contributions_count = request.user.contributions.count()
    approved_contributions_count = request.user.contributions.filter(status="approved").count()

    context = {
        "form": form,
        "profile": profile,
        "contributions_count": contributions_count,
        "approved_contributions_count": approved_contributions_count,
    }
    return render(request, "accounts/profile.html", context)
