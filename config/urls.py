from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Root URL Configuration for Pariksha Platform
urlpatterns = [
    # Core & Health
    path("", include("apps.core.urls")),

    # Accounts & Authentication (Local + Google OAuth via django-allauth)
    path("accounts/", include("apps.accounts.urls")),
    path("accounts/", include("allauth.urls")),

    # Academics Dynamic APIs
    path("academics/", include("apps.academics.urls")),

    # Verified Question Papers & Downloads
    path("papers/", include("apps.papers.urls")),

    # Contributions, Reviewer Workflows & Custom Admin Console
    path("", include("apps.reviews.urls")),

    # Official Syllabus Management
    path("syllabus/", include("apps.syllabus.urls")),

    # Student Dashboard, Ask Pariksha & Preparation Tools
    path("", include("apps.assistant_ui.urls")),

    # Django built-in Administration
    path("django-admin/", admin.site.urls),
]

# Static & Media serving during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom HTTP Error Handlers
handler403 = "apps.core.views.custom_permission_denied_view"
handler404 = "apps.core.views.custom_page_not_found_view"
handler500 = "apps.core.views.custom_server_error_view"
