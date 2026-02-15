# Auth Reference

## Contents
- Multi-Auth Strategy
- Token Validation
- Session Management
- Security Best Practices
- Account Linking Workflow

---

## Multi-Auth Strategy

### Project Authentication Architecture

This project supports four authentication methods tracked via `AuthProvider` model:

| Method | Provider | Backend | Use Case |
|--------|----------|---------|----------|
| Email/Password | `'email'` | `django.contrib.auth.backends.ModelBackend` | Traditional login |
| Google OAuth2 | `'google'` | `social_core.backends.google.GoogleOAuth2` | One-click social login |
| LinkedIn OAuth2 | `'linkedin'` | `social_core.backends.linkedin.LinkedinOAuth2` | Professional network |
| Magic Link | `'magic_link'` | `sesame.backends.ModelBackend` | Passwordless one-time login |

### Authentication Backend Configuration

```python
# config/settings/base.py

AUTHENTICATION_BACKENDS = [
    'sesame.backends.ModelBackend',  # Magic link authentication (must be first)
    'social_core.backends.google.GoogleOAuth2',  # Google login
    'social_core.backends.linkedin.LinkedinOAuth2',  # LinkedIn login
    'django.contrib.auth.backends.ModelBackend',  # Traditional password login
]
```

**Order matters:** Django tries each backend in sequence. Place sesame first so magic link tokens are validated before password checks.

### Track Authentication Method on Login

```python
# GOOD - Always track which method user used
from django.contrib.auth import login
from users.models import AuthProvider

def magic_login_view(request, token):
    user = get_user(token)
    if user is None:
        return render(request, 'registration/magic_link_invalid.html')
    
    # Log user in with sesame backend
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Track that user has used magic link
    AuthProvider.objects.get_or_create(
        user=user,
        provider='magic_link'
    )
    
    return redirect('dashboard')
```

---

## Token Validation

### Validate Token Securely

```python
# GOOD - Use django-sesame's get_user()
from sesame.utils import get_user

def magic_login_view(request, token):
    # get_user() validates:
    # - Token signature (cryptographic verification)
    # - Expiration (SESAME_MAX_AGE = 3600 seconds)
    # - One-time use (SESAME_ONE_TIME = True)
    user = get_user(token)
    
    if user is None:
        # Token is invalid, expired, or already used
        return render(request, 'registration/magic_link_invalid.html', status=400)
    
    login(request, user, backend='sesame.backends.ModelBackend')
    return redirect('dashboard')
```

### DON'T: Manual Token Validation

```python
# BAD - Never roll your own token validation
import hashlib

def magic_login_view(request, token):
    # ❌ INSECURE - Missing expiration, no HMAC, vulnerable to timing attacks
    try:
        user_id = int(token.split('-')[0])
        provided_hash = token.split('-')[1]
        user = CustomUser.objects.get(id=user_id)
        expected_hash = hashlib.md5(f"{user.id}{user.email}".encode()).hexdigest()
        
        if provided_hash == expected_hash:  # ❌ Timing attack vulnerable
            login(request, user)
            return redirect('dashboard')
    except:
        pass
```

**Why this breaks:**
1. **No expiration** - Token valid forever
2. **Weak hashing** - MD5 is cryptographically broken
3. **No HMAC** - Attackers can forge tokens
4. **Timing attack** - String comparison leaks information
5. **No one-time use** - Token can be reused indefinitely

**The Fix:** Always use `sesame.utils.get_user()` and `get_token()` - they handle all security correctly.

---

## Session Management

### Configure Secure Sessions

```python
# config/settings/production.py

# Session expires after 1 hour of inactivity
SESSION_COOKIE_AGE = 3600

# Session expires when browser closes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# HTTPS-only session cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Magic link token expiration (django-sesame)
SESAME_MAX_AGE = 3600  # 1 hour
SESAME_ONE_TIME = True  # Single-use tokens
```

### Session After Magic Link Login

```python
# GOOD - Session created automatically by login()
from django.contrib.auth import login

def magic_login_view(request, token):
    user = get_user(token)
    if user:
        login(request, user, backend='sesame.backends.ModelBackend')
        # Session created with SESSION_COOKIE_AGE expiration
        return redirect('dashboard')
```

### WARNING: Session Fixation

```python
# BAD - Using token as session identifier
def magic_login_view(request, token):
    user = get_user(token)
    if user:
        request.session['magic_token'] = token  # ❌ Don't store tokens
        request.session['user_id'] = user.id
        return redirect('dashboard')
```

**Why this breaks:**
1. **Session fixation** - Attacker can hijack session if token leaked
2. **Token reuse** - Defeats one-time use protection
3. **Session bloat** - Storing unnecessary data in session

**The Fix:** Use Django's `login()` function - it handles session creation securely.

---

## Security Best Practices

### Magic Link Security Settings

```python
# config/settings/base.py

# CRITICAL: Enable one-time use tokens
SESAME_ONE_TIME = True

# Token expires after 1 hour
SESAME_MAX_AGE = 3600

# Only allow magic links from authenticated sources
SESAME_SALT = 'your-unique-salt-value'  # Change this per environment

# Invalidate token after use
SESAME_INVALIDATE_ON_PASSWORD_CHANGE = True
```

### DO: Require Email Verification

```python
# GOOD - Only send magic links to verified emails
from users.models import CustomUser

def request_magic_link_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Only send if email is verified
            if user.email_verified:
                send_magic_link_email(request, user)
            else:
                # Send verification email instead
                send_email_verification(request, user)
            
        except CustomUser.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return render(request, 'registration/magic_link_sent.html')
```

### DON'T: Allow Unverified Email Login

```python
# BAD - Magic link to unverified email = account takeover
def request_magic_link_view(request):
    email = request.POST.get('email')
    user = CustomUser.objects.get(email=email)
    send_magic_link_email(request, user)  # ❌ Sends to unverified email
```

**Why this breaks:**
- Attacker registers with victim's email
- Requests magic link before victim verifies
- Gains access to account

---

## Account Linking Workflow

### Link Magic Link to Existing Account

```python
# GOOD - Allow users to add magic link to password account
from django.contrib.auth.decorators import login_required

@login_required
def enable_magic_link_view(request):
    """
    User with password login wants to enable magic link.
    """
    # Check if magic link already enabled
    has_magic = AuthProvider.objects.filter(
        user=request.user,
        provider='magic_link'
    ).exists()
    
    if has_magic:
        messages.info(request, 'Magic link already enabled.')
        return redirect('user_settings')
    
    if request.method == 'POST':
        # Enable magic link authentication
        AuthProvider.objects.create(
            user=request.user,
            provider='magic_link'
        )
        
        # Send test magic link
        send_magic_link_email(request, request.user)
        
        messages.success(request, 'Magic link enabled. Check your email.')
        return redirect('user_settings')
    
    return render(request, 'users/enable_magic_link.html')
```

### Handle First-Time Magic Link Users

```python
# GOOD - Prompt magic-only users to set password
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    # Check if user only has magic link authentication
    auth_methods = AuthProvider.objects.filter(user=request.user).values_list('provider', flat=True)
    
    if list(auth_methods) == ['magic_link']:
        # User has never set a password
        messages.info(
            request,
            'Add a password to enable email/password login alongside magic links.'
        )
        context = {
            'show_password_prompt': True,
            'set_password_url': reverse('set_password'),
        }
    else:
        context = {'show_password_prompt': False}
    
    return render(request, 'dashboard.html', context)
```

### Account Linking via Token

```python
# users/auth_models.py

class AuthLinkingToken(models.Model):
    """
    Temporary token for linking new auth provider to existing account.
    Used when email matches but user logged in via different method.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        from django.utils import timezone
        return timezone.now() < self.expires_at
```

### Link OAuth to Magic Link Account

```python
# GOOD - Allow linking OAuth to existing magic link account
from social_django.models import UserSocialAuth

def link_oauth_to_account(request, provider):
    """
    User logged in via magic link, wants to add Google/LinkedIn.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if OAuth already linked
    if UserSocialAuth.objects.filter(user=request.user, provider=provider).exists():
        messages.info(request, f'{provider.title()} already linked.')
        return redirect('user_settings')
    
    # Redirect to OAuth flow
    return redirect(f'social:begin', backend=provider)