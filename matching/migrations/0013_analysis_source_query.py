from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0012_profilevacancydiscovery_auto_discard_evaluated_at_and_more"),
        ("operations", "0015_operationalrun_source_funnel"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisSourceQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enqueued_by_query", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("analysis", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_queries", to="matching.vacancyanalysis")),
                ("source_query", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analysis_links", to="operations.operationalrun")),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("source_query", "analysis"), name="unique_analysis_source_query")],
                "indexes": [models.Index(fields=["source_query", "created_at"], name="analysis_query_created_idx")],
            },
        ),
    ]
