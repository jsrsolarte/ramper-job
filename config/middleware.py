from django.contrib.auth import logout


class LogoutInactiveUsersMiddleware:
    """Revoke an existing session as soon as its account is deactivated."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_active:
            logout(request)
        return self.get_response(request)
