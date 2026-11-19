from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0063_returnrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='evidence_image',
            field=models.ImageField(blank=True, null=True, upload_to='return_evidence/'),
        ),
    ]
