import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0017_periodic_refresh_state"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AutomaticSearchSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True)),
                ("starts_at", models.TimeField(default=datetime.time(21, 0))),
                ("ends_at", models.TimeField(default=datetime.time(7, 0))),
                ("updated_at", models.DateTimeField(default=timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="AutomaticSearchScheduleChange",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(default=timezone.now)),
                ("previous_enabled", models.BooleanField()),
                ("previous_starts_at", models.TimeField()),
                ("previous_ends_at", models.TimeField()),
                ("new_enabled", models.BooleanField()),
                ("new_starts_at", models.TimeField()),
                ("new_ends_at", models.TimeField()),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-changed_at"]},
        ),
        # Unknown historical batches are conservatively considered automatic.
        migrations.AddField(
            model_name="refreshbatch",
            name="origin",
            field=models.CharField(choices=[("automatic", "Automática"), ("manual", "Manual")], db_index=True, default="automatic", max_length=12),
        ),
    ]
