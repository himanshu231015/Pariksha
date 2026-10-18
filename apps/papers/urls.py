from django.urls import path
from . import views

app_name = "papers"

urlpatterns = [
    path("", views.paper_list, name="list"),
    path("<int:pk>/", views.paper_detail, name="detail"),
    path("<int:pk>/download/", views.paper_download, name="download"),
    path("<int:pk>/preview/", views.paper_preview, name="preview"),
]
