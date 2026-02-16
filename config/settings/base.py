import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-#9ncyo)*vy7^*r@b6y34y-k02eieu*x1)pb79)poe6e_m2t^w_')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else []

# Application definition
INSTALLED_APPS = [
    # Customizable admin dashboard
    'unfold',
    'unfold.contrib.import_export',
    'unfold.contrib.forms',

    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party apps
    'corsheaders',
    'tailwind',
    'social_django',
    'sesame',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_email',
    'otp_yubikey',
    'two_factor',
    'two_factor.plugins.email',
    'two_factor.plugins.yubikey', 
    'simple_history',
    
    # Local apps
    'theme',
    'users',
    'quick_catch',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'theme'/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('TIME_ZONE', 'America/New_York')
USE_I18N = True
USE_TZ = True

# Two-factor authentication
TWO_FACTOR_PATCH_ADMIN = True
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = 'two_factor:profile'
LOGOUT_REDIRECT_URL = 'two_factor:login'

# Two-factor authentication plugins
TWO_FACTOR_FORCE_OTP_ADMIN = True
TWO_FACTOR_FORCE_OTP_EMAIL = True
TWO_FACTOR_FORCE_OTP_YUBIKEY = True
TWO_FACTOR_REMEMBER_COOKIE_AGE = 60 * 60 * 24 * 30 # 30 days
TWO_FACTOR_REMEMBER_COOKIE_DOMAIN = os.environ.get('TWO_FACTOR_REMEMBER_COOKIE_DOMAIN', '')
TWO_FACTOR_REMEMBER_COOKIE_SECURE = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tailwind configuration
TAILWIND_APP_NAME = 'theme'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Database
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

# Email configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')


SOCIAL_AUTH_JSONFIELD_ENABLED = True
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'sesame.backends.ModelBackend',

)

# Google OAuth2 configuration
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# LinkedIn OAuth2 configuration
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = os.environ.get('LINKEDIN_CLIENT_ID')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ['emailAddress']

# Django Sesame configuration
SESAME_MAX_AGE = 60 * 60  # 1 hour expiration for magic links
SESAME_ONE_TIME = True  # Magic links can only be used once

# LocalAI (OpenAI-compatible) for Quick Catch cognitive triage
LOCALAI_BASE_URL = os.environ.get('LOCALAI_BASE_URL', 'http://localhost:8080/v1')
LOCALAI_MODEL = os.environ.get('LOCALAI_MODEL', 'qwen3')
LOCALAI_API_KEY = os.environ.get('LOCALAI_API_KEY', '')  # Optional; many self-hosted setups use no key
LOCALAI_TIMEOUT = int(os.environ.get('LOCALAI_TIMEOUT', '120'))
