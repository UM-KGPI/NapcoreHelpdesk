from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0011_sourcechunk_doc_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcechunk",
            name="structured_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="OntologyAssetVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ontology_key", models.CharField(max_length=64, unique=True)),
                ("file_path", models.CharField(max_length=512)),
                ("graph_uri", models.CharField(max_length=255)),
                ("version", models.CharField(max_length=64)),
                ("content_hash", models.CharField(max_length=64)),
                ("graphdb_repository", models.CharField(blank=True, max_length=255)),
                ("last_loaded_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["ontology_key"],
            },
        ),
        migrations.CreateModel(
            name="EvidenceProvenance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provenance_id", models.CharField(max_length=128, unique=True)),
                ("core_concepts", models.JSONField(blank=True, default=list)),
                ("ontology_versions", models.JSONField(blank=True, default=list)),
                ("rule_conclusions", models.JSONField(blank=True, default=list)),
                ("provenance_payload", models.JSONField(blank=True, default=dict)),
                (
                    "evidence_link",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="provenance_records", to="helpdesk.answerevidencelink"),
                ),
                (
                    "question_event",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="evidence_provenance_records", to="helpdesk.questionevent"),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="ontologyassetversion",
            index=models.Index(fields=["version"], name="ontology_version_idx"),
        ),
        migrations.AddIndex(
            model_name="ontologyassetversion",
            index=models.Index(fields=["content_hash"], name="ontology_hash_idx"),
        ),
        migrations.AddIndex(
            model_name="evidenceprovenance",
            index=models.Index(fields=["provenance_id"], name="prov_id_idx"),
        ),
        migrations.AddIndex(
            model_name="evidenceprovenance",
            index=models.Index(fields=["question_event"], name="prov_qevent_idx"),
        ),
    ]
