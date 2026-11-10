from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ActiveAccountPasswordResetConfirmView(PasswordResetConfirmView):
    """Require reset links to belong to an active account with a usable password."""

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user and user.is_active and user.has_usable_password():
            return user
        return None


class InactiveAwareAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("El usuario o la contraseña no son correctos. Inténtalo de nuevo."),
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if not username or not password:
            return super().clean()

        self.user_cache = authenticate(self.request, username=username, password=password)
        if self.user_cache is None:
            User = get_user_model()
            try:
                user = User._default_manager.get_by_natural_key(username)
            except User.DoesNotExist:
                user = None
            if user is not None and not user.is_active and user.check_password(password):
                raise ValidationError(
                    _("Tu cuenta está inactiva. Contacta al administrador para recuperar el acceso."),
                    code="inactive_account",
                )
            raise self.get_invalid_login_error()

        self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data
