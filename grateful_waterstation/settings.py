from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Set DJANGO_SECRET_KEY or SECRET_KEY in the environment.')

DEBUG_VALUE = os.environ.get('DJANGO_DEBUG', os.environ.get('DEBUG', 'False'))
DEBUG = DEBUG_VALUE.strip().lower() in {'1', 'true', 'yes', 'on'}

host_values = (
    os.environ.get('ALLOWED_HOSTS', ''),
    os.environ.get('DJANGO_ALLOWED_HOSTS', ''),
    os.environ.get('DJANGO_ALLOWED_HOST', ''),
)
ALLOWED_HOSTS = [
    host.strip()
    for value in host_values
    for host in value.split(',')
    if host.strip()
]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
        '127.0.0.1',
        'localhost',
        '192.168.1.6',
        '192.168.1.145',
        '192.168.254.125',
        '172.24.206.135',
        '10.86.198.135',
    ]
WIFI_CREDENTIALS_BASE_URL = os.environ.get('WIFI_CREDENTIALS_BASE_URL', '').strip().rstrip('/')

# Enable only when requests reach Django through a trusted HTTPS reverse proxy.
TRUST_PROXY_HEADERS = os.environ.get('TRUST_PROXY_HEADERS') == '1'
USE_X_FORWARDED_HOST = TRUST_PROXY_HEADERS
SECURE_PROXY_SSL_HEADER = (
    ('HTTP_X_FORWARDED_PROTO', 'https')
    if TRUST_PROXY_HEADERS
    else None
)
# Map provider tokens for tile access. Set these in your environment or .env file.
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')
CARTO_API_KEY = os.environ.get('CARTO_API_KEY', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'accounts',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.NoStoreCacheMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'grateful_waterstation.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'accounts.context_processors.map_api_keys',
        ],
    },
}]
WSGI_APPLICATION = 'grateful_waterstation.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'neondb'),
        'USER': os.environ.get('DB_USER', 'neondb_owner'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'ep-shiny-art-b3qlglbs-pooler.c-4.ap-southeast-1.aws.neon.tech'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'require'),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'accounts' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}
MEDIA_URL = '/delivery_images/'
MEDIA_ROOT = BASE_DIR / 'delivery_images'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = 'login'
ACCOUNT_LOGIN_REDIRECT_URL = '/accounts/dashboard-redirect/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': True,
    }
}

# Gmail SMTP credentials belong in the local .env file or deployment secrets.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '30'))

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True