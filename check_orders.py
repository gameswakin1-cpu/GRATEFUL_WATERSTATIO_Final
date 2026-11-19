#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grateful_waterstation.settings')
django.setup()

from accounts.models import Order

# Check orders with delivery images
orders_with_photos = Order.objects.filter(delivery_image__isnull=False).values('order_number', 'status', 'delivered_at', 'created_at')
print("Orders WITH delivery photos:")
for order in orders_with_photos[:5]:
    print(f"  Order {order['order_number']}: Status={order['status']}, Delivered={order['delivered_at']}")

# Check pending orders with delivery photos
pending_with_photos = Order.objects.filter(status='pending', delivery_image__isnull=False).count()
print(f"\nPending orders WITH delivery photos: {pending_with_photos}")

# Check delivered orders
delivered_count = Order.objects.filter(status='delivered').count()
print(f"Total delivered orders: {delivered_count}")
