from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Verification for {self.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_for_user(user, email):
        """Create or update verification code for user"""
        code = EmailVerification.generate_code()
        expires_at = timezone.now() + timedelta(minutes=15)  # Valid for 15 minutes
        
        verification, created = EmailVerification.objects.get_or_create(
            user=user,
            defaults={
                'email': email,
                'verification_code': code,
                'expires_at': expires_at,
                'attempts': 0
            }
        )
        
        if not created:
            verification.email = email
            verification.verification_code = code
            verification.expires_at = expires_at
            verification.attempts = 0
            verification.is_verified = False
            verification.save()
        
        return verification
    
    def verify(self, code):
        """Verify the provided code"""
        if self.is_expired():
            return False, "Verification code has expired. Please request a new one."
        
        if self.attempts >= 3:
            return False, "Too many attempts. Please request a new verification code."
        
        self.attempts += 1
        self.save()
        
        if code.strip() == self.verification_code:
            self.is_verified = True
            self.save()
            return True, "Email verified successfully!"
        
        return False, f"Invalid code. {3 - self.attempts} attempts remaining."
