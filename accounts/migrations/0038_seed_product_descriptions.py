from django.db import migrations


PRODUCT_DESCRIPTIONS = {
    'container_5g': (
        'Purified Water\n'
        '20 Liters'
    ),
    'gallon': (
        'Purified Water\n'
        '20 Liters'
    ),
    'bottle_350ml': (
        'Purified Water\n'
        '10 Liters'
    ),
    'distilled': (
        'Purified Water\n'
        '5 Liters'
    ),
}


def seed_product_descriptions(apps, schema_editor):
    Product = apps.get_model('accounts', 'Product')
    for container_type, description in PRODUCT_DESCRIPTIONS.items():
        Product.objects.filter(container_type=container_type).update(description=description)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0037_product_product_type'),
    ]

    operations = [
        migrations.RunPython(seed_product_descriptions, migrations.RunPython.noop),
    ]
