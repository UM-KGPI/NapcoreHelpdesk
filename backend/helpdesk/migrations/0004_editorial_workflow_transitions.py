import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0003_indexedsourcefile_indexrunmetric"),
    ]

    operations = [
        migrations.AlterField(
            model_name="editorialqueueitem",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("review", "Review"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("published", "Published"),
                ],
                default="draft",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="EditorialQueueTransition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("submit_for_review", "Submit for review"),
                            ("request_changes", "Request changes"),
                            ("approve", "Approve"),
                            ("reject", "Reject"),
                            ("publish", "Publish"),
                            ("reopen", "Reopen"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "from_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("review", "Review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("published", "Published"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("review", "Review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("published", "Published"),
                        ],
                        max_length=16,
                    ),
                ),
                ("actor_id", models.CharField(blank=True, max_length=128)),
                ("actor_roles", models.JSONField(blank=True, default=list)),
                ("comment", models.TextField(blank=True)),
                (
                    "queue_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transitions",
                        to="helpdesk.editorialqueueitem",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
