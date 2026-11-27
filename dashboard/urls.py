from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),
    path("por-analizar/", views.pending, name="pending"),
    path("analisis/", views.analysis, name="analysis"),
    path("novedades/revisar/", views.mark_recommendations_reviewed_view, name="mark_recommendations_reviewed"),
    path("vacantes/<int:vacancy_id>/seguimiento/", views.update_follow_up, name="update_follow_up"),
]
