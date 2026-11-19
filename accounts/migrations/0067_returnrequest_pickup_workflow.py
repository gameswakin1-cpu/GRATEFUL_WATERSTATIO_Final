from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def prepare_approved_returns_for_pickup(apps, schema_editor):
    ReturnRequest = apps.get_model('accounts', 'ReturnRequest')
    ReturnRequest.objects.filter(status='approved').update(
        pickup_status='awaiting_assignment'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0066_returnrequest_review_notes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='pickup_status',
            field=models.CharField(
                choices=[
                    ('not_ready', 'Not ready for pickup'),
                    ('awaiting_assignment', 'Awaiting rider assignment'),
                    ('assigned', 'Rider assigned'),
                    ('picked_up', 'Picked up'),
                    ('received', 'Returned to station'),
                ],
                default='not_ready',
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='pickup_rider',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'profile__role': 'rider'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_return_pickups',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='picked_up_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='received_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(
            prepare_approved_returns_for_pickup,
            migrations.RunPython.noop,
        ),
    ]
