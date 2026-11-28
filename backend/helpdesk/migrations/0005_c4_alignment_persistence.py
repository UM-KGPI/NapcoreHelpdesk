import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0004_editorial_workflow_transitions"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcechunk",
            name="embedding_vector",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="FAQEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("faq_entry_id", models.CharField(max_length=128, unique=True)),
                ("normalized_intent", models.CharField(max_length=512)),
                ("standards_scope", models.JSONField(blank=True, default=list)),
                ("keyword_tokens", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["faq_entry_id"],
            },
        ),
        migrations.CreateModel(
            name="AnswerEvidenceLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("evidence_link_id", models.CharField(max_length=128, unique=True)),
                ("answer_id", models.CharField(max_length=128)),
                ("repository_url", models.URLField()),
                ("commit_sha", models.CharField(max_length=64)),
                ("source_path", models.CharField(max_length=512)),
                ("chunk_id", models.CharField(max_length=128)),
                ("label", models.CharField(blank=True, max_length=255)),
                (
                    "question_event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answer_evidence_links",
                        to="helpdesk.questionevent",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RetrievalEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("retrieval_event_id", models.CharField(max_length=128, unique=True)),
                ("repository_url", models.URLField()),
                ("commit_sha", models.CharField(max_length=64)),
                ("source_path", models.CharField(max_length=512)),
                ("chunk_id", models.CharField(max_length=128)),
                ("score", models.FloatField(default=0.0)),
                (
                    "question_event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="retrieval_events",
                        to="helpdesk.questionevent",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="FAQVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version", models.IntegerField(default=1)),
                ("answer", models.TextField()),
                ("citations", models.JSONField(blank=True, default=list)),
                ("confidence", models.FloatField(default=0.85)),
                ("review_required", models.BooleanField(default=False)),
                ("is_published", models.BooleanField(default=True)),
                (
                    "faq_entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="helpdesk.faqentry",
                    ),
                ),
            ],
            options={
                "ordering": ["faq_entry", "-version"],
            },
        ),
        migrations.AddIndex(
            model_name="faqentry",
            index=models.Index(fields=["faq_entry_id"], name="faqentry_id_idx"),
        ),
        migrations.AddIndex(
            model_name="faqentry",
            index=models.Index(fields=["is_active"], name="faqentry_active_idx"),
        ),
        migrations.AddIndex(
            model_name="answerevidencelink",
            index=models.Index(fields=["evidence_link_id"], name="evlink_id_idx"),
        ),
        migrations.AddIndex(
            model_name="answerevidencelink",
            index=models.Index(fields=["answer_id"], name="evlink_answer_idx"),
        ),
        migrations.AddIndex(
            model_name="answerevidencelink",
            index=models.Index(fields=["source_path"], name="evlink_source_idx"),
        ),
        migrations.AddIndex(
            model_name="retrievalevent",
            index=models.Index(fields=["retrieval_event_id"], name="ret_event_id_idx"),
        ),
        migrations.AddIndex(
            model_name="retrievalevent",
            index=models.Index(fields=["repository_url"], name="ret_repo_idx"),
        ),
        migrations.AddIndex(
            model_name="retrievalevent",
            index=models.Index(fields=["source_path"], name="ret_source_idx"),
        ),
        migrations.AddConstraint(
            model_name="faqversion",
            constraint=models.UniqueConstraint(fields=("faq_entry", "version"), name="uniq_faq_version_per_entry"),
        ),
        migrations.AddIndex(
            model_name="faqversion",
            index=models.Index(fields=["is_published"], name="faqversion_pub_idx"),
        ),
    ]
