# Generated migration to fix delivery_image paths

from django.db import migrations

def fix_delivery_image_paths(apps, schema_editor):
    """Remove 'delivery_images/' prefix from stored paths"""
    Order = apps.get_model('accounts', 'Order')
    for order in Order.objects.exclude(delivery_image=''):
        if order.delivery_image and 'delivery_images/' in order.delivery_image.name:
            # Remove the 'delivery_images/' prefix
            order.delivery_image.name = order.delivery_image.name.replace('delivery_images/', '', 1)
            order.save()

def reverse_delivery_image_paths(apps, schema_editor):
    """Reverse the fix (add 'delivery_images/' prefix back)"""
    Order = apps.get_model('accounts', 'Order')
    for order in Order.objects.exclude(delivery_image=''):
        if order.delivery_image and not order.delivery_image.name.startswith('delivery_images/'):
            order.delivery_image.name = 'delivery_images/' + order.delivery_image.name
            order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_remove_userprofile_google_id_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_delivery_image_paths, reverse_delivery_image_paths),
    ]
