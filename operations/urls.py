from django.urls import path

from . import views

app_name = "operations"
urlpatterns = [
    path("", views.admin_center, name="admin_center"),
    path("vacantes/manuales/", views.manual_vacancies, name="manual_vacancies"),
    path("usuarios/", views.users, name="users"),
    path("usuarios/crear/", views.create_user, name="create_user"),
    path("usuarios/<int:user_id>/estado/", views.toggle_user, name="toggle_user"),
    path("usuarios/<int:user_id>/restablecer/", views.request_password_reset, name="request_password_reset"),
    path("observabilidad/", views.dashboard, name="dashboard"),
    path("estadisticas/", views.platform_statistics, name="platform_statistics"),
    path("parametros/", views.parameters, name="parameters"),
    path("comandos/ejecutar/", views.run_command, name="run_command"),
]
