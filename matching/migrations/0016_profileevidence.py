from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0015_aicallattempt_format_action_and_repair_stages"),
        ("profiles", "0008_profile_min_score_stars"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("extractor_version", models.PositiveSmallIntegerField()),
                ("source_sha256", models.CharField(max_length=64)),
                ("facts", models.JSONField(blank=True, default=list)),
                ("input_tokens", models.PositiveIntegerField(blank=True, null=True)),
                ("output_tokens", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("profile_revision", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="evidence_records",
                    to="profiles.profilerevision",
                )),
            ],
            options={
                "verbose_name": "evidencia laboral de CV",
                "verbose_name_plural": "evidencias laborales de CV",
                "ordering": ["-extractor_version", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="profileevidence",
            constraint=models.UniqueConstraint(
                fields=("profile_revision", "extractor_version"),
                name="unique_profile_evidence_revision_extractor",
            ),
        ),
    ]
