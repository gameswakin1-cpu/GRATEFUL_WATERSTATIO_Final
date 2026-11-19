# Google OAuth 2.0 Setup Guide for Django

This guide explains how to set up Google OAuth 2.0 authentication in your Django project using `django-allauth`.

## Redirect URI

For local browser testing, add this exact URI to the Google OAuth client:

```text
http://127.0.0.1:8000/accounts/social/google/login/callback/
```

The URI is based on the hostname and scheme used to open the app. When testing
from a phone over Wi-Fi, the phone uses the computer's LAN IP (for example,
`192.168.1.145`), not `127.0.0.1`. Google OAuth will reject a callback that
does not exactly match an authorized redirect URI. Use a public HTTPS hostname
for phone testing and add its exact callback URI to the Google OAuth client:

```text
https://<public-hostname>/accounts/social/google/login/callback/
```

Plain HTTP access through a LAN IP is not a supported Google OAuth callback.

## Google Cloud Console Setup

Before using Google OAuth, you need to configure the authorized redirect URI in Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, add the local callback for desktop testing:
   ```
   http://127.0.0.1:8000/accounts/social/google/login/callback/
   ```
5. Click **Save**

For phone testing, also add the HTTPS callback URI for the public hostname or
stable HTTPS tunnel used to reach the development server. The host and scheme
must match exactly; restart Django after changing the environment settings below.

## Setup Steps

### 1. Install Required Packages

```bash
pip install django-allauth requests PyJWT
```

`PyJWT` is required by django-allauth to validate Google's OpenID Connect identity
token. It provides the `jwt` module imported during the OAuth callback.

**Note**: `django-allauth` v65.19.2 is already installed in this project.

### 2. Configure settings.py

The following settings have been added to `grateful_waterstation/settings.py`:

#### Installed Apps
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'django.contrib.sites',
    
    # Django Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    'accounts',
]

SITE_ID = 1
```

#### Middleware
```python
MIDDLEWARE = [
    # ... existing middleware ...
    'allauth.account.middleware.AccountMiddleware',
]
```

#### Authentication Backends
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

#### Google OAuth Configuration
```python
# Account settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_METHODS = {'email'}
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Google OAuth 2.0 Configuration (Credentials are in migration 0028)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': True,
    }
}
```

**Note**: The actual credentials (Client ID and Secret) are stored in the database via migration `0028_setup_google_oauth.py`, not in settings.py. This prevents conflicts and allows for easier management.

### 3. Run Migrations

The migration `0028_setup_google_oauth.py` automatically configures the Google OAuth app:

```bash
python manage.py migrate
```

This will:
1. Create the necessary allauth database tables
2. Set up the default site (127.0.0.1:8000)
3. Create the Google SocialApp with your credentials
4. Associate the app with the site

### Phone testing through a trusted HTTPS proxy

When using an HTTPS tunnel or reverse proxy, Django must use the public host
and HTTPS scheme when it builds Google's callback URL. Set these environment
variables before starting Django, replacing the example hostname with the
actual tunnel hostname:

```powershell
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost,<public-hostname>"
$env:TRUST_PROXY_HEADERS = "1"
```

Only enable `TRUST_PROXY_HEADERS` when Django is behind a trusted proxy that
sets `X-Forwarded-Host` and `X-Forwarded-Proto`. Do not enable it when exposing
Django directly to untrusted clients. Add
`https://<public-hostname>/accounts/social/google/login/callback/` to the
Google OAuth client's **Authorized redirect URIs** and open the app on the
phone using that same HTTPS hostname.

### 3. Configure URLs

Added to `grateful_waterstation/urls.py`:

```python
urlpatterns = [
    # ... existing URLs ...
    path('accounts/', include('accounts.urls')),
    # Django Allauth URLs (for Google OAuth)
    path('accounts/social/', include('allauth.urls')),
]
```

### 4. Database Migrations

Run migrations to create the necessary allauth tables:

```bash
python manage.py migrate
```

This creates tables for:
- Social accounts
- Social application tokens
- Social application tokens with sessions
- Email addresses

### 5. Google Login Button

Added to `accounts/templates/accounts/login.html`:

```html
{% load socialaccount %}

<!-- Social Login Divider -->
<div class="social-divider">
    <span class="divider-line"></span>
    <span class="divider-text">or continue with</span>
    <span class="divider-line"></span>
</div>

<!-- Google Login Button -->
<div class="social-login">
    <a href="{% provider_login_url 'google' %}" class="btn-google">
        <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
            <!-- Google SVG paths -->
        </svg>
        <span>Sign in with Google</span>
    </a>
</div>
```

### 6. User Profile View

Created profile view in `accounts/views.py`:

```python
from allauth.socialaccount.models import SocialAccount

@login_required
def user_profile(request):
    user = request.user
    google_account = SocialAccount.objects.filter(user=user, provider='google').first()
    
    context = {
        'user': user,
        'google_account': google_account,
        'is_google_user': google_account is not None,
        'profile_picture': google_account.get_avatar_url() if google_account else None,
        'google_data': google_account.extra_data if google_account else None,
    }
    
    return render(request, 'accounts/user_profile.html', context)
```

### 7. Profile URLs

Added to `accounts/urls.py`:

```python
path('profile/', views.user_profile, name='user_profile'),
path('api/profile/', views.social_profile_info, name='social_profile_api'),
```

## How It Works

1. **Login Flow**:
   - User clicks "Sign in with Google" button
   - Redirected to Google's OAuth consent screen
   - User grants permission
   - Google redirects back to `http://127.0.0.1:8000/accounts/login/`
   - Allauth creates/authenticates user
   - User is redirected to appropriate dashboard based on role

2. **User Creation**:
   - If email doesn't exist: New user is created with Google data
   - If email exists: User is linked to existing account
   - User profile is automatically created via signal

3. **Profile Display**:
   - Visit `/accounts/profile/` to see user info
   - Shows name, email, profile picture from Google
   - Shows account role and permissions

## Usage

### Login URL
- Regular login: `/accounts/login/`
- Google OAuth: Click "Sign in with Google" button

### Profile URL
- View profile: `/accounts/profile/`
- API endpoint: `/accounts/api/profile/`

### Logout URL
- Logout: `/accounts/logout/`

## Features

- ✅ Google OAuth 2.0 integration
- ✅ Automatic user creation/authentication
- ✅ Profile picture from Google
- ✅ Email verification status
- ✅ Session handling
- ✅ Role-based redirect after login
- ✅ User profile information display
- ✅ API endpoint for AJAX profile data

## Security Notes

1. **Production**: Change `DEBUG = False` and use HTTPS
2. **Credentials**: Store client secret in environment variables
3. **Redirect URI**: Update in Google Console for production
4. **Allowed Hosts**: Add production domain to `ALLOWED_HOSTS`

## Troubleshooting

1. **Migration errors**: Run `python manage.py migrate`
2. **Template errors**: Ensure `{% load socialaccount %}` is at the top
3. **OAuth errors**: Check redirect URI matches Google Console settings
4. **Profile not created**: Ensure signals are connected in `models.py`
