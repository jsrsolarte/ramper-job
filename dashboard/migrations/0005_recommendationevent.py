import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_vacancyfollowup_archived_at"),
        ("jobs", "0009_vacancy_url_identity_and_detail_state"),
        ("profiles", "0009_recommendation_tracking"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendation_events", to="profiles.profile")),
                ("vacancy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendation_events", to="jobs.vacancy")),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="recommendationevent",
            constraint=models.UniqueConstraint(fields=("profile", "vacancy"), name="unique_recommendation_event_profile_vacancy"),
        ),
        migrations.AddIndex(
            model_name="recommendationevent",
            index=models.Index(fields=["profile", "created_at"], name="rec_event_profile_created_idx"),
        ),
    ]
