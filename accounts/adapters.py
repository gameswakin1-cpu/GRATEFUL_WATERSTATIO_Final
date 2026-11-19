"""
Custom Django Allauth Adapters
Handles user creation and redirects for social authentication.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social authentication.
    Ensures new users get 'customer' role by default.
    Skips the signup form and auto-creates users.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Hook that runs before the social login process.
        Detects if user is signing up vs logging in, and handles accordingly.
        """
        # If user already exists and social account is connected, just log them in
        if sociallogin.is_existing:
            return
        
        # Get the email from Google
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
        if not email:
            return
        
        from django.contrib.auth.models import User
        from django.contrib import messages
        from django.shortcuts import render
        from allauth.core.exceptions import ImmediateHttpResponse
        from .forms import EmailRegistrationForm

        process = sociallogin.state.get('process', 'login')
        is_signup_flow = process == 'signup'
        if not is_signup_flow:
            referer = request.META.get('HTTP_REFERER', '')
            is_signup_flow = 'register' in referer or 'signup' in request.GET.get('next', '')

        existing_users = list(User.objects.filter(email__iexact=email).order_by('pk')[:2])
        if len(existing_users) > 1:
            messages.error(
                request,
                'More than one account uses this Google email. Please contact support to resolve the duplicate accounts before continuing.'
            )
            template = 'accounts/register.html' if is_signup_flow else 'accounts/login.html'
            context = {'form': EmailRegistrationForm()} if is_signup_flow else None
            raise ImmediateHttpResponse(render(request, template, context))
        
        if existing_users:
            existing_user = existing_users[0]
            if is_signup_flow:
                messages.error(
                    request,
                    f'An account with email {email} already exists. Please log in instead.'
                )
                raise ImmediateHttpResponse(
                    render(request, 'accounts/register.html', {'form': EmailRegistrationForm()})
                )

            sociallogin.connect(request, existing_user)
            return

        if process == 'login':
            messages.error(
                request,
                f'No account found with email {email}. Please sign up first.'
            )
            raise ImmediateHttpResponse(render(request, 'accounts/login.html'))
        
        # Auto-signup: skip the signup form (only for signup flow)
        sociallogin.state['process'] = 'login'

    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and ensure profile is created with 'customer' role.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Ensure UserProfile is created with 'customer' role
        from .models import Consumer, UserProfile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'customer'}
        )
        user.profile = profile
        
        # If profile exists but has no role or different role, set to customer
        if not created and not profile.role:
            profile.role = 'customer'
            profile.save()

        if sociallogin.account.provider == 'google':
            Consumer.objects.get_or_create(user=user)
            request.session['google_profile_completion_user_id'] = user.pk
        
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Let Google users reach the dashboard before completing their profile.
        """
        return True

    def populate_user(self, request, sociallogin, data):
        """
        Populate user data from Google OAuth response.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get data from Google
        email = data.get('email', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Generate username from email (before @ symbol) + random suffix to ensure uniqueness
        import re
        import random
        if email:
            base_username = re.sub(r'[^\w]', '', email.split('@')[0])[:20]
            # Check if username exists, add random suffix if needed
            from django.contrib.auth.models import User
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{random.randint(1000, 9999)}"
            user.username = username
        
        # Set names from Google
        user.first_name = first_name
        user.last_name = last_name
        
        # Ensure email is set
        user.email = email
        
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Return the URL to redirect to after successfully connecting a social account.
        """
        return resolve_url('user_profile')


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for regular account authentication.
    """

    def get_login_redirect_url(self, request):
        """
        Redirect to dashboard based on user role after login.
        """
        user = request.user
        
        # Check if user has a profile with role
        if hasattr(user, 'profile') and user.profile:
            role = user.profile.role
            if role == 'admin':
                return resolve_url('admin_dashboard')
            elif role == 'staff':
                return resolve_url('staff_dashboard')
            elif role == 'rider':
                return resolve_url('rider_dashboard')
            else:
                return resolve_url('customer_dashboard')
        
        # Default redirect if no profile
        return resolve_url('dashboard_redirect')

    def get_logout_redirect_url(self, request):
        """
        Redirect to login page after logout.
        """
        return resolve_url('login')
