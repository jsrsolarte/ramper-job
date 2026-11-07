from django.urls import path

from . import views

app_name = "profiles"
urlpatterns = [
    path("", views.edit_profile, name="edit"),
    path("cv/", views.download_cv, name="cv"),
]
