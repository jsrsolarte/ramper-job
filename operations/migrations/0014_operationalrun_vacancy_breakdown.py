from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0013_applicant_activity_auto_deactivation"),
    ]

    operations = [
        migrations.AddField(
            model_name="operationalrun",
            name="new_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="operationalrun",
            name="known_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="operationalrun",
            name="known_updated_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="operationalrun",
            name="known_unchanged_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
