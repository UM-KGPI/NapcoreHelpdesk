"""GIN index for the text search of retrieval_gateway._lexical_recall_candidates.

Its expression must stay identical to retrieval_gateway.TEXT_SEARCH_MATCH, or PostgreSQL will not use it.
Built CONCURRENTLY (so the migration is not atomic): answers keep working while it builds. SQLite, used by
no deployment, skips it.
"""

from django.db import migrations

INDEX = "sourcechunk_text_tsv_gin_idx"


def create(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX} ON helpdesk_sourcechunk "
            "USING gin (to_tsvector('english'::regconfig, text))"
        )


def drop(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX}")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("helpdesk", "0021_editoraccount")]

    operations = [migrations.RunPython(create, drop)]
