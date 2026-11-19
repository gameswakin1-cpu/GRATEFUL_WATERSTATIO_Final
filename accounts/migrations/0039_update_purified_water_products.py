from django.db import migrations


PRODUCT_DETAILS = {
    'container_5g': ('Blue Water Dispend Round Container', 'Purified Water\n20 Liters'),
    'gallon': ('Gallon Blue Water Container', 'Purified Water\n20 Liters'),
    'bottle_350ml': ('Gallon Slim Container', 'Purified Water\n10 Liters'),
    'distilled': ('Grateful Purified Water', 'Purified Water\n5 Liters'),
}


def update_product_details(apps, schema_editor):
    Product = apps.get_model('accounts', 'Product')
    for container_type, (name, description) in PRODUCT_DETAILS.items():
        Product.objects.filter(container_type=container_type).update(
            name=name,
            description=description,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0038_seed_product_descriptions'),
    ]

    operations = [
        migrations.RunPython(update_product_details, migrations.RunPython.noop),
    ]
