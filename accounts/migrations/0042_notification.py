from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0041_order_delivery_details'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('orders', 'Orders'), ('inventory', 'Inventory'), ('maintenance', 'IoT/Maintenance'), ('riders', 'Riders'), ('users', 'Users')], default='orders', max_length=20)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('warning', 'Warning'), ('info', 'Info')], default='info', max_length=10)),
                ('target_url', models.CharField(blank=True, max_length=300)),
                ('is_read', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='app_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
