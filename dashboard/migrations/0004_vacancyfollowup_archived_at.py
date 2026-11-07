from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_vacancyfollowup_state_changed_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="vacancyfollowup",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="vacancyfollowup",
            index=models.Index(fields=["archived_at", "state_changed_at"], name="followup_archive_due_idx"),
        ),
    ]
