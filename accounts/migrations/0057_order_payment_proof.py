from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0056_order_payment_proof'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_proof',
            field=models.ImageField(blank=True, null=True, upload_to='payment_proofs/'),
        ),
    ]
