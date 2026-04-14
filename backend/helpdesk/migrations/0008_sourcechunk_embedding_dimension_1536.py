import helpdesk.db_fields
from django.db import migrations


class Migration(migrations.Migration):
    """Increase the embedding vector dimension from 64 to 1536.

    This aligns the schema with real embedding models (e.g. text-embedding-3-small).
    Existing indexed chunks keep their 64-dimensional vectors in the JSON/pgvector column
    but will return cosine_similarity=0.0 against new 1536-dim query vectors until
    re-indexed. Re-run the index command for all repositories after applying this migration.

    PostgreSQL/pgvector: this alters the vector(64) column type to vector(1536).
    SQLite: the underlying JSONField stores arrays of any length; no structural change needed.
    """

    dependencies = [
        ("helpdesk", "0007_alter_sourcechunk_embedding_vector"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sourcechunk",
            name="embedding_vector",
            field=helpdesk.db_fields.PortableVectorField(blank=True, default=list, dimensions=1536),
        ),
    ]
