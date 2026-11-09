from django.conf import settings
from django.db import migrations, models


def exempt_users_who_already_logged_in(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Progress = apps.get_model("profiles", "GuidedTourProgress")
    database = schema_editor.connection.alias
    existing_ids = set(
        Progress.objects.using(database)
        .filter(owner__last_login__isnull=False, owner__is_staff=False, owner__is_superuser=False)
        .values_list("owner_id", flat=True)
    )
    Progress.objects.using(database).filter(owner_id__in=existing_ids).update(mandatory_completed=True)
    missing = User.objects.using(database).filter(
        last_login__isnull=False,
        is_staff=False,
        is_superuser=False,
    ).exclude(pk__in=existing_ids)
    Progress.objects.using(database).bulk_create(
        [Progress(owner_id=user_id, mandatory_completed=True) for user_id in missing.values_list("pk", flat=True)],
        batch_size=500,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0005_guidedtourprogress"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="guidedtourprogress",
            name="mandatory_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(exempt_users_who_already_logged_in, migrations.RunPython.noop),
    ]
