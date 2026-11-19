import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grateful_waterstation.settings')
django.setup()

from accounts.models import Product

# Check current state of Distilled Water product
try:
    product = Product.objects.get(name='Distilled Water')
    print(f"Product found: {product.name}")
    print(f"Container type: {product.container_type}")
    print(f"Price: PHP {product.price}")
    print(f"Stock: {product.stock_quantity}")
    
    # Force update container_type
    product.container_type = 'distilled'
    product.save()
    print(f"Force updated container_type to distilled")
    
except Product.DoesNotExist:
    print("Distilled Water product not found. Creating it...")
    product = Product.objects.create(
        name='Distilled Water',
        price=60.00,
        water_type='mineral',
        container_type='distilled',
        stock_quantity=100,
        reorder_level=10,
        is_active=True
    )
    print(f"Created product: {product.name} - PHP {product.price}")
