import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0015_operationalrun_source_funnel"),
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RefreshBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("queued", "En cola"), ("running", "En curso"), ("succeeded", "Completada"), ("partial", "Parcial"), ("failed", "Fallida")], default="queued", max_length=16)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("heartbeat_at", models.DateTimeField(db_index=True, default=timezone.now)),
                ("planned_at", models.DateTimeField(blank=True, null=True)),
                ("command", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="refresh_batches", to="operations.admincommandrun")),
            ],
        ),
        migrations.CreateModel(
            name="RefreshBatchProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("lease_token", models.CharField(max_length=120)),
                ("source_results", models.JSONField(blank=True, default=dict)),
                ("found_vacancy_ids", models.JSONField(blank=True, default=list)),
                ("search_request", models.JSONField(blank=True, default=dict)),
                ("failed", models.BooleanField(default=False)),
                ("stale", models.BooleanField(default=False)),
                ("prepared_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profiles", to="operations.refreshbatch")),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="profiles.profile")),
                ("profile_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refresh_profiles", to="operations.operationalrun")),
            ],
        ),
        migrations.AddConstraint(
            model_name="refreshbatchprofile",
            constraint=models.UniqueConstraint(fields=("batch", "profile"), name="ops_refresh_batch_profile_uniq"),
        ),
        migrations.CreateModel(
            name="RefreshWorkItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(db_index=True, max_length=80)),
                ("identity", models.CharField(max_length=64)),
                ("search_request", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("queued", "En cola"), ("running", "En curso"), ("succeeded", "Completada"), ("partial", "Parcial"), ("failed", "Fallida")], db_index=True, default="queued", max_length=16)),
                ("phase", models.CharField(choices=[("titles", "Búsqueda"), ("details", "Fichas"), ("complete", "Completada")], default="titles", max_length=12)),
                ("cursor", models.PositiveIntegerField(default=0)),
                ("listings", models.JSONField(blank=True, default=list)),
                ("listing_count", models.PositiveIntegerField(default=0)),
                ("title_kept_count", models.PositiveIntegerField(default=0)),
                ("title_discarded_count", models.PositiveIntegerField(default=0)),
                ("details_requested_count", models.PositiveIntegerField(default=0)),
                ("details_received_count", models.PositiveIntegerField(default=0)),
                ("title_input_tokens", models.PositiveIntegerField(blank=True, null=True)),
                ("available", models.BooleanField(default=True)),
                ("error_category", models.CharField(blank=True, max_length=80)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("lease_token", models.CharField(blank=True, max_length=120)),
                ("lease_expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("heartbeat_at", models.DateTimeField(db_index=True, default=timezone.now)),
                ("last_dispatched_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_items", to="operations.refreshbatch")),
                ("source_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refresh_work_items", to="operations.operationalrun")),
            ],
        ),
        migrations.AddConstraint(
            model_name="refreshworkitem",
            constraint=models.UniqueConstraint(fields=("batch", "source", "identity"), name="ops_refresh_work_identity_uniq"),
        ),
        migrations.AddIndex(
            model_name="refreshworkitem",
            index=models.Index(fields=["status", "lease_expires_at"], name="ops_refresh_work_lease_idx"),
        ),
        migrations.AddIndex(
            model_name="refreshworkitem",
            index=models.Index(fields=["batch", "status"], name="ops_ref_work_batch_state_idx"),
        ),
        migrations.CreateModel(
            name="RefreshWorkProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_id", models.PositiveBigIntegerField()),
                ("batch_profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="work_links", to="operations.refreshbatchprofile")),
                ("work_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profile_links", to="operations.refreshworkitem")),
            ],
        ),
        migrations.AddConstraint(
            model_name="refreshworkprofile",
            constraint=models.UniqueConstraint(fields=("work_item", "batch_profile"), name="ops_refresh_work_profile_uniq"),
        ),
    ]
