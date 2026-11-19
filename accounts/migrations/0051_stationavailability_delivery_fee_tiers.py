from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0050_stationavailability_delivery_fee'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stationavailability',
            name='delivery_fee',
        ),
        migrations.AddField(
            model_name='stationavailability',
            name='delivery_fee_up_to_2km',
            field=models.DecimalField(decimal_places=2, default=20, max_digits=10),
        ),
        migrations.AddField(
            model_name='stationavailability',
            name='delivery_fee_up_to_3km',
            field=models.DecimalField(decimal_places=2, default=30, max_digits=10),
        ),
        migrations.AddField(
            model_name='stationavailability',
            name='delivery_fee_up_to_5km',
            field=models.DecimalField(decimal_places=2, default=40, max_digits=10),
        ),
        migrations.AddField(
            model_name='stationavailability',
            name='delivery_fee_over_5km',
            field=models.DecimalField(decimal_places=2, default=50, max_digits=10),
        ),
    ]
