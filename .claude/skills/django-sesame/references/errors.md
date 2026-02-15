# Errors Reference

## Contents
- Token Validation Errors
- Email Sending Failures
- Rate Limiting Errors
- Session Errors
- Migration Errors

---

## Token Validation Errors

### Invalid Token Error

**Symptom:** `get_user(token)` returns `None`

**Causes:**
1. Token expired (older than `SESAME_MAX_AGE`)
2. Token already used (`SESAME_ONE_TIME = True`)
3. Token signature invalid (tampered)
4. User no longer exists

```python
# GOOD - Handle all None cases gracefully
from sesame.utils import get_user
import logging

logger = logging.getLogger(__name__)

def magic_login_view(request, token):
    user = get_user(token)
    
    if user is None:
        logger.warning(
            f"Invalid magic link attempt from IP: {request.META.get('REMOTE_ADDR')}"
        )
        return render(request, 'registration/magic_link_invalid.html', {
            'error': 'This link is invalid, expired, or has already been used.',
            'action': 'request_magic_link',
        }, status=400)
    
    login(request, user, backend='sesame.backends.ModelBackend')
    AuthProvider.objects.get_or_create(user=user, provider='magic_link')
    return redirect('dashboard')
```

### DON'T: Expose Token State

```python
# BAD - Reveals too much information
def magic_login_view(request, token):
    user = get_user(token)
    
    if user is None:
        return HttpResponse("Token expired or already used")  # ❌ Security leak
```

**Why this breaks:** Attackers learn token characteristics, aiding brute force attempts.

---

## Email Sending Failures

### SMTP Connection Error

**Symptom:** `smtplib.SMTPException` or `ConnectionRefusedError`

**Causes:**
1. Invalid `EMAIL_HOST` or `EMAIL_PORT`
2. Firewall blocking SMTP
3. Missing email credentials

```python
# GOOD - Graceful fallback with logging
from django.core.mail import send_mail
from django.core.mail.backends.console import EmailBackend
import logging

logger = logging.getLogger(__name__)

def send_magic_link_email(request, user):
    token = get_token(user)
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[token])
    )
    
    try:
        send_mail(
            subject='Your Login Link',
            message=f'Click to log in: {magic_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Magic link sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send magic link to {user.email}: {str(e)}")
        
        # In development, fall back to console output
        if settings.DEBUG:
            print(f"DEBUG: Magic link for {user.email}:\n{magic_url}\n")
            return True
        
        return False
```

### Gmail "Less Secure Apps" Error

**Symptom:** `smtplib.SMTPAuthenticationError: (535, b'Username and Password not accepted')`

**Cause:** Gmail blocked login from Django app

**Fix:** Use App-Specific Password

```python
# config/settings/base.py

# DON'T use your Gmail password directly
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')  # your-email@gmail.com
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # App-specific password

# Get app password from: https://myaccount.google.com/apppasswords
```

**Steps to fix:**
1. Enable 2-factor authentication on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Use generated password in `EMAIL_HOST_PASSWORD`

---

## Rate Limiting Errors

### Redis Connection Error

**Symptom:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Cause:** Redis not running or wrong connection URL

```python
# GOOD - Fallback to in-memory cache if Redis unavailable
# config/settings/development.py

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# config/settings/production.py

import os

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        }
    }
}
```

### Cache Key Collision

**Symptom:** Rate limiting affects wrong users

**Cause:** Non-unique cache keys

```python
# BAD - Cache key collision
def request_magic_link_view(request):
    cache_key = 'magic_link_requests'  # ❌ Same key for all users
    request_count = cache.get(cache_key, 0)
```

**Fix:** Include user identifier in cache key

```python
# GOOD - Unique cache key per user/IP
def request_magic_link_view(request):
    email = request.POST.get('email')
    
    # Rate limit by email AND IP
    email_key = f'magic_link_email:{email}'
    ip_key = f'magic_link_ip:{request.META.get("REMOTE_ADDR")}'
    
    email_requests = cache.get(email_key, 0)
    ip_requests = cache.get(ip_key, 0)
    
    if email_requests >= 3 or ip_requests >= 5:
        return HttpResponseTooManyRequests("Rate limit exceeded")
```

---

## Session Errors

### "User object has no attribute 'backend'"

**Symptom:** `AttributeError: 'CustomUser' object has no attribute 'backend'`

**Cause:** Missing backend parameter in `login()` call

```python
# BAD - No backend specified
from django.contrib.auth import login

def magic_login_view(request, token):
    user = get_user(token)
    if user:
        login(request, user)  # ❌ Missing backend
```

**Fix:** Always specify sesame backend

```python
# GOOD - Explicit backend
def magic_login_view(request, token):
    user = get_user(token)
    if user:
        login(request, user, backend='sesame.backends.ModelBackend')  # ✓
```

### Session Not Persisting After Magic Link Login

**Symptom:** User logged in but immediately logged out on next request

**Cause:** Session middleware missing or misconfigured

```python
# config/settings/base.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # ← Must be here
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ← After SessionMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

## Migration Errors

### "relation 'users_authprovider' does not exist"

**Symptom:** `ProgrammingError: relation "users_authprovider" does not exist`

**Cause:** Migrations not applied

**Fix:** Run migrations

```bash
# Check migration status
python manage.py showmigrations users

# Apply pending migrations
python manage.py migrate users

# If migration file missing, create it
python manage.py makemigrations users
python manage.py migrate
```

### Duplicate AuthProvider Entries

**Symptom:** `IntegrityError: duplicate key value violates unique constraint "users_authprovider_user_id_provider_key"`

**Cause:** Concurrent requests creating same AuthProvider

**Fix:** Use `get_or_create()` with atomic transaction

```python
# GOOD - Thread-safe creation
from django.db import transaction

@transaction.atomic
def track_authentication_method(user, provider):
    auth_provider, created = AuthProvider.objects.get_or_create(
        user=user,
        provider=provider
    )
    
    if not created:
        # Already exists, update timestamp
        auth_provider.save(update_fields=['last_used'])
    
    return auth_provider
```

### Migration Rollback Error

**Symptom:** `django.db.migrations.exceptions.IrreversibleError`

**Cause:** Data migration without reverse operation

**Fix:** Add reverse function to data migration

```python
# users/migrations/0003_populate_auth_providers.py

from django.db import migrations

def populate_auth_providers(apps, schema_editor):
    # Forward migration
    CustomUser = apps.get_model('users', 'CustomUser')
    AuthProvider = apps.get_model('users', 'AuthProvider')
    # ... create entries

def reverse_populate(apps, schema_editor):
    # Reverse migration - REQUIRED
    AuthProvider = apps.get_model('users', 'AuthProvider')
    AuthProvider.objects.filter(provider='email').delete()

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(
            populate_auth_providers,
            reverse_populate  # ← Add this
        ),
    ]
```

---

## Common Error Patterns

### Magic Link Not Clickable in Email

**Symptom:** Email shows `/users/magic/AbCdEf/` as plain text

**Cause:** Using relative URL instead of absolute

```python
# BAD - Relative URL
magic_url = reverse('magic_login', args=[token])
# Result: /users/magic/AbCdEf/ (not clickable)
```

**Fix:** Use `build_absolute_uri()`

```python
# GOOD - Absolute URL
magic_url = request.build_absolute_uri(
    reverse('magic_login', args=[token])
)
# Result: https://yourdomain.com/users/magic/AbCdEf/ (clickable)
```

### HTTPS Redirect Breaking Tokens

**Symptom:** Magic link redirects to homepage, losing token

**Cause:** `SECURE_SSL_REDIRECT` forcing HTTPS, but email sent HTTP URL

**Fix:** Force HTTPS in URL generation

```python
# GOOD - Force HTTPS in production
def send_magic_link_email(request, user):
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[get_token(user)])
    )
    
    # Force HTTPS in production
    if not settings.DEBUG:
        magic_url = magic_url.replace('http://', 'https://')
    
    send_mail(message=f'Login: {magic_url}', ...)