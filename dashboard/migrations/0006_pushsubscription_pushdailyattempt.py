import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0005_recommendationevent"),
        ("profiles", "0009_recommendation_tracking"),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint_digest", models.CharField(max_length=64, unique=True)),
                ("endpoint_ciphertext", models.TextField()),
                ("p256dh_ciphertext", models.TextField()),
                ("auth_ciphertext", models.TextField()),
                ("active", models.BooleanField(default=True)),
                ("activated_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_event_cutoff_id", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_subscriptions", to="profiles.profile")),
            ],
            options={"verbose_name": "suscripción de notificaciones", "verbose_name_plural": "suscripciones de notificaciones"},
        ),
        migrations.AddIndex(
            model_name="pushsubscription",
            index=models.Index(fields=["profile", "active"], name="push_sub_profile_active_idx"),
        ),
        migrations.CreateModel(
            name="PushDailyAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subscription_digest", models.CharField(max_length=64)),
                ("local_date", models.DateField()),
                ("status", models.CharField(choices=[("reserved", "Reservado"), ("sent", "Aceptado por el servicio push"), ("failed", "Fallido o resultado incierto")], default="reserved", max_length=12)),
                ("failure_category", models.CharField(blank=True, max_length=32)),
                ("reserved_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="daily_attempts", to="dashboard.pushsubscription")),
            ],
            options={"verbose_name": "intento de resumen push", "verbose_name_plural": "intentos de resumen push"},
        ),
        migrations.AddConstraint(
            model_name="pushdailyattempt",
            constraint=models.UniqueConstraint(fields=("subscription_digest", "local_date"), name="unique_push_digest_local_day"),
        ),
        migrations.AddIndex(
            model_name="pushdailyattempt",
            index=models.Index(fields=["local_date", "status"], name="push_attempt_day_status_idx"),
        ),
    ]
