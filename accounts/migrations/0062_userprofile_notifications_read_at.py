from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0061_wificonfiguration'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='notifications_read_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
