from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse

from profiles.tour import ensure_mandatory_tour, is_tour_eligible, step_by_id


class LogoutInactiveUsersMiddleware:
    """Revoke an existing session as soon as its account is deactivated."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_active:
            logout(request)
        return self.get_response(request)


class MandatoryGuidedTourMiddleware:
    """Limit first-time aspirants to the pages needed by the required guide."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if not is_tour_eligible(user):
            return self.get_response(request)

        progress = ensure_mandatory_tour(user)
        if progress is None:
            return self.get_response(request)
        request.mandatory_tour_pending = True
        request.mandatory_tour_step = progress.current_step

        try:
            view_name = resolve(request.path_info).view_name
        except Resolver404:
            view_name = ""
        if (
            view_name in {"healthz", "readyz", "logout", "profiles:tour_state", "profiles:tour_action"}
            or view_name.startswith(("operations:", "admin:"))
        ):
            return self.get_response(request)

        current_step = step_by_id(progress.current_step)
        required_path = reverse(current_step["url_name"])
        if request.method == "GET" and request.path_info == required_path:
            return self.get_response(request)
        return redirect(required_path)
