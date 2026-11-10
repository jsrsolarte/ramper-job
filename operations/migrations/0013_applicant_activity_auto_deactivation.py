from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def populate_applicant_activity(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Activity = apps.get_model("operations", "ApplicantActivity")
    database = schema_editor.connection.alias
    rows = []
    for user in User.objects.using(database).all().iterator():
        last_activity = user.last_login or user.date_joined or timezone.now()
        rows.append(Activity(user_id=user.pk, last_authenticated_activity=last_activity))
        if len(rows) >= 500:
            Activity.objects.using(database).bulk_create(rows, ignore_conflicts=True)
            rows = []
    if rows:
        Activity.objects.using(database).bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0012_alter_adminauditevent_action"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ApplicantActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_authenticated_activity", models.DateTimeField(db_index=True, default=timezone.now)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="applicant_activity", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(populate_applicant_activity, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="adminauditevent",
            name="actor",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="admin_audit_actions", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="adminauditevent",
            name="action",
            field=models.CharField(choices=[
                ("account_created", "Cuenta creada"),
                ("account_deactivated", "Cuenta desactivada"),
                ("account_auto_deactivated", "Desactivada por inactividad"),
                ("account_reactivated", "Cuenta reactivada"),
                ("invitation_created", "Invitación creada"),
                ("invitation_revoked", "Invitación revocada"),
                ("invitation_accepted", "Invitación aceptada"),
                ("password_reset_requested", "Recuperación solicitada"),
                ("password_reset_delivery_failed", "Fallo de entrega de recuperación"),
                ("password_reset_link_generated", "Enlace de restablecimiento generado"),
                ("password_reset_unavailable", "Recuperación no disponible"),
                ("processing_paused", "Procesamiento pausado"),
                ("processing_resumed", "Procesamiento reanudado"),
            ], max_length=40),
        ),
    ]
