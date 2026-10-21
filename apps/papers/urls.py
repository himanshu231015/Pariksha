from django.urls import path
from . import views

app_name = "papers"

urlpatterns = [
    path("", views.paper_list, name="list"),
    path("subject/<int:subject_id>/", views.subject_papers, name="subject_papers"),
    path("<int:pk>/", views.paper_detail, name="detail"),
    path("<int:pk>/download/", views.paper_download, name="download"),
    path("<int:pk>/preview/", views.paper_preview, name="preview"),
    path("<int:pk>/solution/download/", views.solution_download, name="solution_download"),
    path("<int:pk>/solution/preview/", views.solution_preview, name="solution_preview"),
    path("<int:pk>/solution/upload/", views.upload_solution, name="upload_solution"),
    path("<int:pk>/solution/delete/", views.delete_solution, name="delete_solution"),
]
