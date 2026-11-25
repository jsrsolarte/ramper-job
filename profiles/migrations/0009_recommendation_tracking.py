import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0008_profile_min_score_stars"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="recommendation_tracking_started_at",
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="recommendations_reviewed_through",
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
