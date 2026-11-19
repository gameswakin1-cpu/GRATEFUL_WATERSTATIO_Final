from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0064_returnrequest_evidence_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnRequestImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='return_evidence/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('return_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidence_images', to='accounts.returnrequest')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
    ]
