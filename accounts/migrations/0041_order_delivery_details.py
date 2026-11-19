from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0040_order_subtotal_order_delivery_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_distance_km',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_area',
            field=models.CharField(default='Talon 3', max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_fee_requires_approval',
            field=models.BooleanField(default=False),
        ),
    ]
