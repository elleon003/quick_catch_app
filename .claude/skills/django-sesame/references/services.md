# Services Reference

## Contents
- Email Integration
- Token Generation
- User Lookup Patterns
- Audit Logging
- Rate Limiting

---

## Email Integration

### Magic Link Email Service

```python
# users/services.py

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from sesame.utils import get_token
import logging

logger = logging.getLogger(__name__)

def send_magic_link_email(request, user):
    """
    Generate and send magic link to user's email.
    Returns True if email sent successfully, False otherwise.
    """
    try:
        token = get_token(user)
        magic_url = request.build_absolute_uri(
            reverse('magic_login', args=[token])
        )
        
        # Force HTTPS in production
        if not settings.DEBUG:
            magic_url = magic_url.replace('http://', 'https://')
        
        send_mail(
            subject=f'Login to {settings.SITE_NAME}',
            message=f'Click here to log in:\n\n{magic_url}\n\nThis link expires in 1 hour.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Magic link sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send magic link to {user.email}: {e}")
        return False
```

### DON'T: Send Tokens in Plain Text Logs

```python
# BAD - Token exposed in logs
def send_magic_link_email(request, user):
    token = get_token(user)
    logger.info(f"Generated token: {token} for {user.email}")  # ❌ SECURITY RISK
```

**Why this breaks:**
1. **Log leakage** - Logs may be stored in insecure locations
2. **Token theft** - Anyone with log access can impersonate users
3. **Compliance violation** - GDPR/HIPAA violations if logs are compromised

**The Fix:** Never log tokens, only log that a token was sent

---

## Token Generation

### Single-Use Token Pattern

```python
# GOOD - Generate fresh token each request
from sesame.utils import get_token
from django.core.cache import cache

def generate_rate_limited_token(user):
    """
    Generate token with rate limiting to prevent abuse.
    Max 3 tokens per hour per user.
    """
    cache_key = f'magic_link_requests:{user.id}'
    request_count = cache.get(cache_key, 0)
    
    if request_count >= 3:
        raise ValueError('Rate limit exceeded. Try again in 1 hour.')
    
    token = get_token(user)
    
    # Increment rate limit counter
    cache.set(cache_key, request_count + 1, timeout=3600)
    
    return token
```

### WARNING: Reusing Tokens

```python
# BAD - Storing and reusing tokens
class CustomUser(AbstractBaseUser):
    magic_token = models.CharField(max_length=255, blank=True)  # ❌
    
def get_or_create_token(user):
    if not user.magic_token:
        user.magic_token = get_token(user)
        user.save()
    return user.magic_token  # ❌ Reused indefinitely
```

**Why this breaks:**
1. **Long-lived tokens** - Token never expires, permanent backdoor
2. **No revocation** - Can't invalidate token if compromised
3. **Defeats one-time use** - User can share link with others
4. **Database bloat** - Storing tokens that django-sesame generates on-the-fly

**The Fix:** Always generate fresh tokens. Django-sesame handles expiration and one-time use automatically with `SESAME_ONE_TIME = True`.

---

## User Lookup Patterns

### Safe User Retrieval

```python
# GOOD - Handle non-existent users gracefully
from users.models import CustomUser
from django.shortcuts import get_object_or_404

def request_magic_link_by_email(request, email):
    """
    Send magic link without revealing if user exists.
    """
    try:
        user = CustomUser.objects.get(email=email)
        send_magic_link_email(request, user)
    except CustomUser.DoesNotExist:
        # Don't reveal if email exists
        pass
    
    # Always show success message (security best practice)
    return render(request, 'registration/magic_link_sent.html', {
        'email': email
    })
```

### DON'T: Leak User Existence

```python
# BAD - Reveals if email exists in database
def request_magic_link_by_email(request, email):
    try:
        user = CustomUser.objects.get(email=email)
        send_magic_link_email(request, user)
        return HttpResponse("Email sent!")
    except CustomUser.DoesNotExist:
        return HttpResponse("User not found", status=404)  # ❌ Information leak
```

**Why this breaks:**
- **Enumeration attack** - Attackers can discover valid email addresses
- **Privacy violation** - Reveals who has accounts
- **Spam target** - Confirmed emails become spam targets

---

## Audit Logging

### Track Magic Link Authentication

```python
# GOOD - Log authentication events for security
from users.models import AuthProvider
import logging

logger = logging.getLogger('security')

def magic_login_view(request, token):
    user = get_user(token)
    
    if user is None:
        logger.warning(f"Invalid magic link attempt from IP: {request.META.get('REMOTE_ADDR')}")
        return render(request, 'registration/magic_link_invalid.html')
    
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Track authentication method
    AuthProvider.objects.get_or_create(user=user, provider='magic_link')
    
    # Log successful login
    logger.info(f"Magic link login: {user.email} from IP: {request.META.get('REMOTE_ADDR')}")
    
    return redirect('dashboard')
```

### Multi-Auth Tracking Service

```python
# users/services.py

from users.models import AuthProvider

def track_authentication_method(user, provider_name):
    """
    Track which authentication methods user has used.
    provider_name: 'email', 'google', 'linkedin', 'magic_link'
    """
    auth_provider, created = AuthProvider.objects.get_or_create(
        user=user,
        provider=provider_name
    )
    
    if created:
        logger.info(f"New auth provider '{provider_name}' added for {user.email}")
    
    # Update last_used timestamp
    auth_provider.save()
    
    return auth_provider
```

---

## Rate Limiting

### Prevent Magic Link Abuse

```python
# GOOD - Rate limit magic link requests
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests

def request_magic_link_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Rate limit by IP
        ip_address = request.META.get('REMOTE_ADDR')
        cache_key = f'magic_link_ip:{ip_address}'
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 5:
            return HttpResponseTooManyRequests(
                "Too many requests. Try again in 1 hour."
            )
        
        # Rate limit by email
        email_cache_key = f'magic_link_email:{email}'
        email_requests = cache.get(email_cache_key, 0)
        
        if email_requests >= 3:
            # Still return success (don't reveal rate limit)
            return render(request, 'registration/magic_link_sent.html')
        
        # Process request
        try:
            user = CustomUser.objects.get(email=email)
            send_magic_link_email(request, user)
            
            # Increment counters
            cache.set(cache_key, request_count + 1, timeout=3600)
            cache.set(email_cache_key, email_requests + 1, timeout=3600)
        except CustomUser.DoesNotExist:
            pass
        
        return render(request, 'registration/magic_link_sent.html')
```

### WARNING: No Rate Limiting

```python
# BAD - Allows unlimited magic link requests
def request_magic_link_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = CustomUser.objects.get(email=email)
        send_magic_link_email(request, user)  # ❌ No rate limiting
```

**Why this breaks:**
1. **Email bombing** - Attacker floods user's inbox
2. **Resource exhaustion** - SMTP server overwhelmed
3. **Cost attack** - Transactional email costs spike
4. **Token flood** - Generates thousands of tokens per second

**The Fix:** Use Redis (see **redis** skill) or Django's cache framework for rate limiting. See **redis** skill for production caching patterns.