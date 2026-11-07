import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0007_single_platform_admin"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("account_created", "Cuenta creada"), ("account_deactivated", "Cuenta desactivada"), ("account_reactivated", "Cuenta reactivada"), ("password_reset_requested", "Recuperación solicitada"), ("password_reset_delivery_failed", "Fallo de entrega de recuperación"), ("password_reset_unavailable", "Recuperación no disponible")], max_length=40)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admin_audit_actions", to=settings.AUTH_USER_MODEL)),
                ("target", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admin_audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
