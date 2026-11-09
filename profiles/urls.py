from django.urls import path

from . import views

app_name = "profiles"
urlpatterns = [
    path("", views.edit_profile, name="edit"),
    path("cv/", views.download_cv, name="cv"),
    path("recorrido/estado/", views.guided_tour_state, name="tour_state"),
    path("recorrido/accion/", views.guided_tour_action, name="tour_action"),
]
