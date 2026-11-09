from django.contrib.auth.views import PasswordResetConfirmView


class ActiveAccountPasswordResetConfirmView(PasswordResetConfirmView):
    """Require reset links to belong to an active account with a usable password."""

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user and user.is_active and user.has_usable_password():
            return user
        return None
