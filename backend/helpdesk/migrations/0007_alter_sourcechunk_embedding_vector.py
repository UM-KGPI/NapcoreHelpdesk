import helpdesk.db_fields
from django.db import migrations


def _convert_embedding_vector_to_native(schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE helpdesk_sourcechunk
            ALTER COLUMN embedding_vector TYPE vector(64)
            USING CASE
                WHEN embedding_vector IS NULL THEN NULL
                ELSE embedding_vector::text::vector(64)
            END
            """
        )


def convert_embedding_vector_to_native(apps, schema_editor):
    _convert_embedding_vector_to_native(schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0006_pgvector_native_alignment"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    convert_embedding_vector_to_native,
                    migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="sourcechunk",
                    name="embedding_vector",
                    field=helpdesk.db_fields.PortableVectorField(blank=True, default=list, dimensions=64),
                )
            ],
        ),
    ]