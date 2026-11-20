from django.contrib.admin import AdminSite


class PlatformAdminSite(AdminSite):
    site_header = "Jobs · Administración"
    site_title = "Administración Jobs"
    index_title = "Herramientas internas"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff and request.user.is_superuser
