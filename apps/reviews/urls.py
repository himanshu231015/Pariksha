from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    # Student paper contribution endpoints
    path("contribute/", views.contribute_paper, name="contribute"),
    path("my-contributions/", views.my_contributions, name="my_contributions"),
    path("contributions/<int:pk>/file/", views.contribution_file_download, name="contribution_file"),

    # Reviewer endpoints
    path("reviewer/dashboard/", views.reviewer_dashboard, name="dashboard"),
    path("reviewer/review/<int:pk>/", views.review_detail, name="review_detail"),

    # Administrator custom dashboard
    path("admin-console/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-console/audit-logs/", views.admin_audit_logs, name="admin_audit_logs"),
]
