from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.urls import include, path
from profiles.views import download_private_cv

urlpatterns = [
    path("admin/operaciones/", include("operations.urls")),
    path("admin/", RedirectView.as_view(pattern_name="operations:admin_center", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password-reset/confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("accounts/password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path("private-media/<path:file_path>", download_private_cv, name="private_cv"),
    path("", include("dashboard.urls")),
    path("perfil/", include("profiles.urls")),
]
