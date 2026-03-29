import helpdesk.db_fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0006_pgvector_native_alignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sourcechunk",
            name="embedding_vector",
            field=helpdesk.db_fields.PortableVectorField(blank=True, default=list, dimensions=64),
        ),
    ]