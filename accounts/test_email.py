import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grateful_waterstation.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 50)
print("EMAIL CONFIGURATION TEST")
print("=" * 50)
print(f"Backend: {settings.EMAIL_BACKEND}")
print(f"Host: {getattr(settings, 'EMAIL_HOST', 'N/A')}")
print(f"Port: {getattr(settings, 'EMAIL_PORT', 'N/A')}")
print(f"User: {getattr(settings, 'EMAIL_HOST_USER', 'N/A')}")
print("=" * 50)

try:
    send_mail(
        'Test Email',
        'If you receive this, your email is working!',
        settings.DEFAULT_FROM_EMAIL,
        ['gameswakin1@gmail.com'],
        fail_silently=False,
    )
    print("✓ Email sent successfully!")
except Exception as e:
    print(f"✗ Failed: {e}")