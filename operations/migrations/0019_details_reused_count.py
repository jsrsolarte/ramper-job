from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("operations", "0018_automatic_search_schedule")]

    operations = [
        migrations.AddField(
            model_name="operationalrun",
            name="details_reused_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="refreshworkitem",
            name="details_reused_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
