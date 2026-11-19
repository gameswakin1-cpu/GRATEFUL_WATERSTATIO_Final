from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_alter_order_status_payment_received'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
