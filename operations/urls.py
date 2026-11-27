from django.urls import path

from . import views

app_name = "operations"
urlpatterns = [
    path("", views.admin_center, name="admin_center"),
    path("horario/estado/", views.schedule_status, name="schedule_status"),
    path("horario/estado-admin/", views.admin_schedule_status, name="admin_schedule_status"),
    path("alertas/dispositivos/", views.operational_alert_push_subscription, name="operational_alert_push_subscription"),
    path("alertas/<int:incident_id>/reconocer/", views.acknowledge_operational_incident, name="acknowledge_operational_incident"),
    path("vacantes/limpiar/", views.vacancy_cleanup, name="vacancy_cleanup"),
    path("vacantes/limpiar/<int:operation_id>/recuperar/", views.retry_vacancy_cleanup, name="retry_vacancy_cleanup"),
    path("vacantes/manuales/", views.manual_vacancies, name="manual_vacancies"),
    path("usuarios/", views.users, name="users"),
    path("usuarios/<int:user_id>/estadisticas/", views.applicant_statistics, name="applicant_statistics"),
    path("usuarios/crear/", views.create_user, name="create_user"),
    path("usuarios/invitar/", views.create_invitation, name="create_invitation"),
    path("usuarios/invitaciones/<int:invitation_id>/revocar/", views.revoke_invitation, name="revoke_invitation"),
    path("usuarios/<int:user_id>/estado/", views.toggle_user, name="toggle_user"),
    path("usuarios/<int:user_id>/restablecer/", views.request_password_reset, name="request_password_reset"),
    path("observabilidad/", views.dashboard, name="dashboard"),
    path("estadisticas/", views.platform_statistics, name="platform_statistics"),
    path("parametros/", views.parameters, name="parameters"),
    path("comandos/ejecutar/", views.run_command, name="run_command"),
]
