from django.db import migrations


def ensure_vector_extension(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")


def create_vector_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS sourcechunk_embedding_ivfflat_idx
            ON helpdesk_sourcechunk
            USING ivfflat (embedding_vector vector_cosine_ops)
            WITH (lists = 100)
            """
        )


def drop_vector_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS sourcechunk_embedding_ivfflat_idx")


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0005_c4_alignment_persistence"),
    ]

    operations = [
        migrations.RunPython(ensure_vector_extension, migrations.RunPython.noop),
        migrations.RunPython(create_vector_index, drop_vector_index),
    ]
