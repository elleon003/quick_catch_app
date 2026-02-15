# Routes Reference

## Contents
- URL Configuration
- View Patterns
- Token URL Structure
- Redirect Strategies
- Common Routing Errors

---

## URL Configuration

### Magic Link URL Pattern

```python
# users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Magic link endpoint - token is passed as URL parameter
    path('magic/<str:token>/', views.magic_login_view, name='magic_login'),
    
    # Request magic link form
    path('request-magic-link/', views.request_magic_link_view, name='request_magic_link'),
]
```

**Why this structure:**
- Token in URL path (not query param) prevents accidental logging in web server logs
- Named URL pattern allows `reverse()` for building URLs
- `<str:token>` accepts django-sesame's alphanumeric tokens

### Root URL Integration

```python
# config/urls.py

from django.urls import path, include

urlpatterns = [
    path('users/', include('users.urls')),
    path('', include('social_django.urls', namespace='social')),
]
```

**Full magic link URL:** `https://yourdomain.com/users/magic/AbCdEf123XyZ/`

---

## View Patterns

### DO: Handle Invalid Tokens Gracefully

```python
# GOOD - Proper error handling with user feedback
from sesame.utils import get_user
from django.contrib.auth import login
from django.shortcuts import render, redirect

def magic_login_view(request, token):
    user = get_user(token)
    
    if user is None:
        # Token invalid, expired, or already used
        return render(request, 'registration/magic_link_invalid.html', {
            'error_type': 'invalid_token',
            'help_text': 'Request a new magic link to continue.'
        }, status=400)
    
    # Log user in with sesame backend
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Track authentication method (project-specific)
    from users.models import AuthProvider
    AuthProvider.objects.get_or_create(user=user, provider='magic_link')
    
    return redirect('dashboard')
```

### DON'T: Expose Token Validation Details

```python
# BAD - Information leakage about token state
def magic_login_view(request, token):
    user = get_user(token)
    
    if user is None:
        # NEVER reveal why token failed
        return HttpResponse("Token expired at 2025-01-01 14:32:15")  # ❌
```

**Why this breaks:**
1. **Security risk** - Attackers learn token expiration times
2. **Brute force aid** - Reveals timing information for guessing
3. **Privacy leak** - Confirms whether email exists in system

---

## Token URL Structure

### Building Absolute URLs

```python
# GOOD - Always use absolute URLs for email links
from django.urls import reverse

def send_magic_link(request, user):
    token = get_token(user)
    
    # build_absolute_uri converts relative to absolute
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[token])
    )
    # Result: https://yourdomain.com/users/magic/AbCdEf123XyZ/
    
    send_mail(
        subject='Your Login Link',
        message=f'Click to log in: {magic_url}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
```

### DON'T: Use Relative URLs in Emails

```python
# BAD - Relative URLs don't work in emails
def send_magic_link(request, user):
    token = get_token(user)
    magic_url = reverse('magic_login', args=[token])
    # Result: /users/magic/AbCdEf123XyZ/  ❌ Not clickable in email!
    
    send_mail(
        message=f'Click: {magic_url}',  # Broken link
        # ...
    )
```

**Why this breaks:**
- Email clients can't resolve relative URLs
- Users see `/users/magic/...` as plain text, not a link
- No domain means the link goes nowhere

---

## Redirect Strategies

### Smart Post-Login Redirects

```python
# GOOD - Redirect based on user context
def magic_login_view(request, token):
    user = get_user(token)
    if user is None:
        return render(request, 'registration/magic_link_invalid.html')
    
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Check if user came from a specific page
    next_url = request.GET.get('next')
    if next_url and is_safe_url(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    
    # Default redirect based on user state
    if not user.has_usable_password():
        # Magic-only user, suggest setting password
        return redirect('set_password')
    
    return redirect('dashboard')
```

### WARNING: Unvalidated Redirects

```python
# BAD - Open redirect vulnerability
def magic_login_view(request, token):
    user = get_user(token)
    if user:
        login(request, user, backend='sesame.backends.ModelBackend')
        next_url = request.GET.get('next')
        return redirect(next_url)  # ❌ Can redirect to evil.com
```

**Why this breaks:**
1. **Phishing vector** - Attacker sends `?next=https://evil.com`
2. **Credential theft** - User thinks they're on your site, enters password on fake page
3. **OWASP vulnerability** - A10:2021 – Server-Side Request Forgery

**The Fix:** Always validate redirects with `is_safe_url()` or Django's `url_has_allowed_host_and_scheme()`

---

## Common Routing Errors

### Error: "NoReverseMatch at /users/request-magic-link/"

**Cause:** URL name mismatch between `reverse()` and urlpatterns

```python
# BAD - URL name doesn't match
urlpatterns = [
    path('magic/<str:token>/', views.magic_login_view, name='magic_link'),
]

# In view:
reverse('magic_login', args=[token])  # ❌ Looking for 'magic_login'
```

**Fix:** Ensure URL names match exactly

```python
# GOOD - Consistent naming
urlpatterns = [
    path('magic/<str:token>/', views.magic_login_view, name='magic_login'),
]

reverse('magic_login', args=[token])  # ✓ Matches
```

### Error: Token URLs Not Working in Production

**Cause:** HTTPS redirect breaking token URLs

```python
# config/settings/production.py

# BAD - Forces HTTPS, but magic links sent via HTTP
SECURE_SSL_REDIRECT = True

# Email sends: http://yourdomain.com/users/magic/...
# Django redirects to: https://yourdomain.com/ (loses token)
```

**Fix:** Always generate HTTPS URLs in production

```python
# GOOD - Force HTTPS in URL generation
def send_magic_link(request, user):
    token = get_token(user)
    
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[token])
    )
    
    # In production, force HTTPS scheme
    if not settings.DEBUG:
        magic_url = magic_url.replace('http://', 'https://')
    
    send_mail(message=f'Login: {magic_url}', ...)
```

### Error: "User object has no attribute 'backend'"

**Cause:** Missing backend parameter in `login()` call

```python
# BAD - No backend specified
from django.contrib.auth import login

login(request, user)  # ❌ django-sesame won't work
```

**Fix:** Always specify `sesame.backends.ModelBackend`

```python
# GOOD - Explicit backend
login(request, user, backend='sesame.backends.ModelBackend')
```

**Why this matters:** Django caches the authentication backend used. Without specifying sesame's backend, subsequent requests may fail authentication checks.