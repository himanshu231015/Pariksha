from django.urls import path
from . import views

app_name = "assistant_ui"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("assistant/", views.assistant_chat_view, name="chat"),
    path("assistant/api/apply-context/", views.api_apply_context, name="api_apply_context"),
    path("assistant/api/ask/", views.api_ask_question, name="api_ask_question"),
    path("preparation/must-prepare/", views.must_prepare_view, name="must_prepare"),
    path("preparation/predicted-paper/", views.predicted_paper_view, name="predicted_paper"),
]
