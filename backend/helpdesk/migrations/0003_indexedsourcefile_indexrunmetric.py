from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0002_sourcechunk"),
    ]

    operations = [
        migrations.CreateModel(
            name="IndexedSourceFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("repository_url", models.URLField()),
                ("source_path", models.CharField(max_length=512)),
                ("commit_sha", models.CharField(max_length=64)),
                ("content_hash", models.CharField(max_length=64)),
            ],
            options={
                "ordering": ["repository_url", "source_path"],
            },
        ),
        migrations.CreateModel(
            name="IndexRunMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("repository_url", models.URLField()),
                ("repository_path", models.CharField(max_length=1024)),
                ("profile", models.CharField(default="default", max_length=64)),
                (
                    "mode",
                    models.CharField(
                        choices=[("full", "Full"), ("incremental", "Incremental")],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "Success"), ("failed", "Failed")],
                        max_length=32,
                    ),
                ),
                ("scanned_files", models.IntegerField(default=0)),
                ("skipped_files", models.IntegerField(default=0)),
                ("created_chunks", models.IntegerField(default=0)),
                ("updated_chunks", models.IntegerField(default=0)),
                ("deleted_chunks", models.IntegerField(default=0)),
                ("duration_ms", models.IntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="indexedsourcefile",
            constraint=models.UniqueConstraint(
                fields=("repository_url", "source_path"),
                name="uniq_indexed_source_file_repo_path",
            ),
        ),
    ]
