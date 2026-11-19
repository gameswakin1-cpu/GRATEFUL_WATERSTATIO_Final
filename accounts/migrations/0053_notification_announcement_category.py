from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0052_remove_delivery_fee_5km_tiers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='category',
            field=models.CharField(
                choices=[
                    ('orders', 'Orders'),
                    ('announcement', 'Announcement'),
                    ('inventory', 'Inventory'),
                    ('maintenance', 'IoT/Maintenance'),
                    ('riders', 'Riders'),
                    ('users', 'Users'),
                ],
                default='orders',
                max_length=20,
            ),
        ),
    ]
