from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0013_questionevent_user_feedback"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionevent",
            name="answer_success",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="questionevent",
            name="citation_click_count",
            field=models.IntegerField(default=0),
        ),
    ]
