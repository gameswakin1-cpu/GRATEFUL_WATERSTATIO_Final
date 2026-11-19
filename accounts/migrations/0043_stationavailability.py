from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0042_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='StationAvailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_open', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
