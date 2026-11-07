from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0006_generalize_operational_parameter_values"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX "auth_one_platform_superuser" ON "auth_user" ("is_superuser") WHERE "is_superuser" = TRUE',
            reverse_sql='DROP INDEX "auth_one_platform_superuser"',
        ),
    ]
