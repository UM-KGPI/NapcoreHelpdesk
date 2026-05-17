from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0012_ontology_provenance_and_structure"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionevent",
            name="user_dislikes",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="questionevent",
            name="user_likes",
            field=models.BooleanField(default=False),
        ),
    ]
