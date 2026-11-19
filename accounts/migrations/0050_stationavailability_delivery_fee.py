from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_maintenancereport_due_date_maintenancereport_photo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stationavailability',
            name='delivery_fee',
            field=models.DecimalField(decimal_places=2, default=20, max_digits=10),
        ),
    ]
