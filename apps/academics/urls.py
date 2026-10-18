from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    path("api/programs/", views.api_programs, name="api_programs"),
    path("api/branches/", views.api_branches, name="api_branches"),
    path("api/semesters/", views.api_semesters, name="api_semesters"),
    path("api/subjects/", views.api_subjects, name="api_subjects"),
    path("api/units/", views.api_units, name="api_units"),
]
