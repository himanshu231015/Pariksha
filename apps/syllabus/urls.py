from django.urls import path
from . import views

app_name = "syllabus"

urlpatterns = [
    path("", views.syllabus_list, name="list"),
    path("upload/", views.syllabus_upload, name="upload"),
    path("<int:pk>/toggle-publish/", views.syllabus_toggle_publish, name="toggle_publish"),
    path("<int:pk>/download/", views.syllabus_download, name="download"),
    path("<int:pk>/preview/", views.syllabus_preview, name="preview"),
]
