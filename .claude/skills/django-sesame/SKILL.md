---
name: django-sesame
description: |
  Implements passwordless magic link authentication with one-time tokens
  Use when: Adding magic link login, passwordless authentication, or one-time access URLs
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Django-sesame Skill

Django-sesame provides cryptographically-signed one-time tokens for passwordless authentication. This project uses it for magic link login alongside traditional email/password and OAuth2 authentication, tracked via the AuthProvider model.

## Quick Start

### Generate and Send Magic Link

```python
from sesame.utils import get_token
from django.urls import reverse
from django.core.mail import send_mail

def send_magic_link(request, user):
    token = get_token(user)
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[token])
    )
    
    send_mail(
        subject='Your Login Link',
        message=f'Click here to log in: {magic_url}',
        from_email='noreply@yourdomain.com',
        recipient_list=[user.email],
    )
```

### Validate Magic Link in View

```python
from sesame.utils import get_user
from django.contrib.auth import login

def magic_login_view(request, token):
    user = get_user(token)  # Returns None if invalid/expired
    if user is None:
        return render(request, 'registration/magic_link_invalid.html')
    
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Track this authentication method (this project's pattern)
    from users.models import AuthProvider
    AuthProvider.objects.get_or_create(
        user=user,
        provider='magic_link'
    )
    
    return redirect('dashboard')
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| Token Generation | `get_token(user)` | `token = get_token(request.user)` |
| Token Validation | `get_user(token)` | `user = get_user(token)` returns None if invalid |
| One-Time Tokens | `SESAME_ONE_TIME = True` | Token invalidated after first use |
| Expiration | `SESAME_MAX_AGE = 3600` | Token expires after 1 hour (3600 seconds) |
| Authentication Backend | Add to AUTHENTICATION_BACKENDS | `'sesame.backends.ModelBackend'` |

## Common Patterns

### Account Recovery via Magic Link

**When:** User forgot password or needs quick access without password

```python
from users.forms import MagicLinkForm

def request_magic_link_view(request):
    if request.method == 'POST':
        form = MagicLinkForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                send_magic_link(request, user)
                return render(request, 'registration/magic_link_sent.html')
            except CustomUser.DoesNotExist:
                # Don't reveal if email exists (security)
                return render(request, 'registration/magic_link_sent.html')
    else:
        form = MagicLinkForm()
    return render(request, 'registration/request_magic_link.html', {'form': form})
```

### Admin-Generated Access Links

**When:** Support needs to grant temporary access to a user

```python
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def generate_user_access_link(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    token = get_token(user)
    magic_url = request.build_absolute_uri(
        reverse('magic_login', args=[token])
    )
    
    # Log this action for audit trail
    logger.info(f"Admin {request.user.email} generated magic link for {user.email}")
    
    return JsonResponse({'magic_url': magic_url})
```

### Multi-Auth Account Linking

**When:** User with magic link wants to set password or link OAuth

```python
from django.contrib.auth.decorators import login_required

@login_required
def link_password_to_account(request):
    # User logged in via magic link, now setting password
    if request.method == 'POST':
        form = PasswordSetForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            AuthProvider.objects.get_or_create(
                user=request.user,
                provider='email'
            )
            messages.success(request, 'Password set successfully')
            return redirect('user_settings')
    else:
        form = PasswordSetForm(request.user)
    return render(request, 'users/set_password.html', {'form': form})
```

## Configuration Reference

```python
# config/settings/base.py

AUTHENTICATION_BACKENDS = [
    'sesame.backends.ModelBackend',  # Magic link authentication
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'django.contrib.auth.backends.ModelBackend',  # Traditional password
]

# Magic link expires after 1 hour
SESAME_MAX_AGE = 3600

# Single-use tokens (recommended for security)
SESAME_ONE_TIME = True
```

## See Also

- [routes](references/routes.md) - URL patterns for magic link endpoints
- [auth](references/auth.md) - Multi-auth strategy with magic links
- [services](references/services.md) - Email service integration
- [errors](references/errors.md) - Magic link error handling
- [database](references/database.md) - AuthProvider model for tracking magic link usage

## Related Skills

- **django** - Framework integration patterns
- **python** - Email sending and URL generation
- **django-social-auth** - Multi-auth account linking patterns