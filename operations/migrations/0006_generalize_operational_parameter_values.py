from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0005_operationalparameter_operationalparameterchange"),
    ]

    operations = [
        migrations.RenameField(
            model_name="operationalparameter",
            old_name="value_minutes",
            new_name="value",
        ),
        migrations.RenameField(
            model_name="operationalparameterchange",
            old_name="previous_value_minutes",
            new_name="previous_value",
        ),
        migrations.RenameField(
            model_name="operationalparameterchange",
            old_name="new_value_minutes",
            new_name="new_value",
        ),
    ]
