from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0051_stationavailability_delivery_fee_tiers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stationavailability',
            name='delivery_fee_up_to_5km',
        ),
        migrations.RemoveField(
            model_name='stationavailability',
            name='delivery_fee_over_5km',
        ),
    ]