from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0009_backfill_completed_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchingconfig",
            name="prompt_version",
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]
