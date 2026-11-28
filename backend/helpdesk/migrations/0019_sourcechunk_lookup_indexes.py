from django.db import migrations

# Retrieval looks up chunks by substring: element tags in the text
# (`text LIKE '%<StopPlace %'`) and words in the path or label
# (`UPPER(source_path) LIKE UPPER('%stopplace%')`). Without an index each lookup
# scans every chunk. Trigram GIN indexes answer the same LIKE queries from the
# index, so results are unchanged. The path and label indexes are on the exact
# expressions Django generates for `icontains`.
TRIGRAM_INDEXES = {
    "sourcechunk_text_trgm_idx": "(text gin_trgm_ops)",
    "sourcechunk_path_upper_trgm_idx": "(UPPER(source_path::text) gin_trgm_ops)",
    "sourcechunk_label_upper_trgm_idx": "(UPPER(label::text) gin_trgm_ops)",
}

# indexed_commit_shas() asks for the newest chunk of a repository whose commit is a
# full SHA. Reading the repository's chunks newest first lets it stop at the first
# match instead of scanning and sorting all of them.
LOOKUP_INDEXES = {
    "sourcechunk_repo_updated_idx": "(repository_url, updated_at DESC)",
}


def create_trigram_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        for name, definition in TRIGRAM_INDEXES.items():
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON helpdesk_sourcechunk USING gin {definition}")
        for name, definition in LOOKUP_INDEXES.items():
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON helpdesk_sourcechunk {definition}")


def drop_trigram_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name in [*TRIGRAM_INDEXES, *LOOKUP_INDEXES]:
            cursor.execute(f"DROP INDEX IF EXISTS {name}")


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0018_indexedsourcefile_schema_references"),
    ]

    operations = [
        migrations.RunPython(create_trigram_indexes, drop_trigram_indexes),
    ]
