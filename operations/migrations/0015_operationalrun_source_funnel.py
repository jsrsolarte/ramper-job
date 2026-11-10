from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0014_operationalrun_vacancy_breakdown"),
    ]

    operations = [
        migrations.AddField("operationalrun", "listing_count", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "title_kept_count", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "title_discarded_count", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "details_requested_count", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "details_received_count", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "title_input_tokens", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "listing_fetch_duration_ms", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "title_preselection_duration_ms", models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField("operationalrun", "detail_fetch_duration_ms", models.PositiveIntegerField(blank=True, null=True)),
    ]
