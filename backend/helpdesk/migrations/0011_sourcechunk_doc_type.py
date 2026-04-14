from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0010_sourcechunk_structure_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcechunk",
            name="doc_type",
            field=models.CharField(blank=True, default="guide", max_length=32),
        ),
    ]
