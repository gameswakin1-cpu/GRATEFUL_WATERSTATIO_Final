from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0065_returnrequestimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='review_notes',
            field=models.TextField(blank=True),
        ),
    ]
