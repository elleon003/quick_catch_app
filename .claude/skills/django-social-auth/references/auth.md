# Auth Reference

Multi-auth strategy, account linking, security patterns, and permission management.

## Contents
- Multi-Auth Strategy
- Account Linking Security
- Password vs Passwordless Users
- Session Management
- Anti-Patterns

---

## Multi-Auth Strategy

### Overview

This project supports four authentication methods:
1. **Email/Password** - Traditional Django authentication
2. **Google OAuth2** - Social login via Google
3. **LinkedIn OAuth2** - Professional network login
4. **Magic Links** - One-time passwordless login via django-sesame

Users can link multiple methods to one account.

### Authentication Flow Decision Tree

```python
# users/views.py
def determine_auth_flow(user):
    """Determine which auth methods user has enabled"""
    providers = AuthProvider.objects.filter(user=user, is_active=True)
    
    has_password = user.has_usable_password()
    has_google = providers.filter(provider_name='google').exists()
    has_linkedin = providers.filter(provider_name='linkedin').exists()
    
    return {
        'can_login_password': has_password,
        'can_login_google': has_google,
        'can_login_linkedin': has_linkedin,
        'can_request_magic_link': True,  # Always available if email exists
        'total_methods': providers.count() + (1 if has_password else 0),
    }
```

### Template: Show Available Login Methods

```html
<!-- theme/templates/registration/login.html -->
{% load static %}

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Sign In</h2>
    
    <!-- Email/Password Form -->
    <form method="post">
      {% csrf_token %}
      <!-- form fields -->
      <button type="submit" class="btn btn-primary">Sign In</button>
    </form>
    
    <div class="divider">OR</div>
    
    <!-- Social Login Buttons -->
    <a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.GET.next|urlencode }}"
       class="btn btn-outline gap-2">
      <svg><!-- Google icon --></svg>
      Sign in with Google
    </a>
    
    <a href="{% url 'social:begin' 'linkedin-oauth2' %}?next={{ request.GET.next|urlencode }}"
       class="btn btn-outline gap-2">
      <svg><!-- LinkedIn icon --></svg>
      Sign in with LinkedIn
    </a>
    
    <div class="divider">OR</div>
    
    <!-- Magic Link -->
    <button hx-post="{% url 'users:request_magic_link' %}"
            hx-include="[name='email']"
            class="btn btn-ghost">
      Email me a login link
    </button>
  </div>
</div>
```

---

## Account Linking Security

### Prevent Unauthorized Account Linking

```python
# users/pipeline.py
from django.contrib.auth import authenticate

def verify_user_before_linking(backend, user, request, *args, **kwargs):
    """
    Require user to be authenticated before linking social account.
    Prevents attacker linking their Google to victim's account.
    """
    if request.user.is_authenticated:
        # User is logged in, safe to link
        return {'user': request.user}
    
    # Not logged in - check for linking token
    token_value = request.session.get('linking_token')
    if token_value:
        try:
            token = AuthLinkingToken.objects.get(token=token_value)
            if token.is_valid():
                return {'user': token.user}
        except AuthLinkingToken.DoesNotExist:
            pass
    
    # No authenticated user - proceed with normal social auth
    return None
```

### Template: Protected Account Linking

```html
<!-- theme/templates/users/auth_settings.html -->
{% load static %}

<div class="card">
  <div class="card-body">
    <h3 class="card-title">Connected Accounts</h3>
    
    {% if has_google %}
      <div class="flex justify-between items-center">
        <span>Google</span>
        {% if can_unlink %}
          <button hx-post="{% url 'users:unlink_provider' 'google' %}"
                  hx-confirm="Remove Google login?"
                  class="btn btn-sm btn-error">
            Unlink
          </button>
        {% else %}
          <span class="badge badge-warning">Last method</span>
        {% endif %}
      </div>
    {% else %}
      <a href="{% url 'users:link_provider' 'google-oauth2' %}"
         class="btn btn-primary">
        Link Google Account
      </a>
    {% endif %}
  </div>
</div>
```

---

## Password vs Passwordless Users

### Checking User Authentication Type

```python
# users/views.py
def get_user_auth_status(user):
    """Determine if user has password or is passwordless"""
    has_password = user.has_usable_password()
    social_auths = UserSocialAuth.objects.filter(user=user)
    
    return {
        'has_password': has_password,
        'is_passwordless': not has_password and social_auths.exists(),
        'social_providers': list(social_auths.values_list('provider', flat=True)),
    }
```

### Setting Password for Social-Only Users

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm

@login_required
def set_password_view(request):
    """Allow passwordless users to set a password"""
    if request.user.has_usable_password():
        return redirect('users:settings')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            
            # Create AuthProvider record for email auth
            AuthProvider.objects.create(
                user=request.user,
                provider_name='email',
                provider_user_id=request.user.email,
            )
            
            messages.success(request, 'Password created successfully!')
            return redirect('users:settings')
    else:
        form = SetPasswordForm(request.user)
    
    return render(request, 'users/set_password.html', {'form': form})
```

---

## Session Management

### Configure Session Timeout for OAuth

```python
# config/settings/base.py

# Session expires when browser closes (default)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Session timeout: 2 weeks
SESSION_COOKIE_AGE = 1209600  # 14 days in seconds

# Session security
SESSION_COOKIE_SECURE = True  # HTTPS only (production)
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

### Remember Me Functionality

```python
# users/views.py
from django.contrib.auth import login

def login_view(request):
    if request.method == 'POST':
        # ... authenticate user ...
        
        remember_me = request.POST.get('remember_me')
        if remember_me:
            request.session.set_expiry(1209600)  # 2 weeks
        else:
            request.session.set_expiry(0)  # Browser close
        
        login(request, user)
        return redirect('users:dashboard')
```

### Social Auth Session Configuration

```python
# config/settings/base.py

# Store social auth data in session during pipeline
SOCIAL_AUTH_SESSION_EXPIRATION = False  # Don't expire OAuth data

# Clean up partial pipelines after 5 minutes
SOCIAL_AUTH_IMMUTABLE_USER_FIELDS = ['email']
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']
```

---

## WARNING: Auth Security Anti-Patterns

### Problem: Allowing Account Linking While Logged Out

```python
# BAD - No authentication check before linking
@login_required  # Not enough! Attacker can start flow logged in as themselves
def link_provider_view(request, provider):
    # Starts OAuth flow
    return redirect('social:begin', backend=provider)

# Attacker flow:
# 1. Log in as attacker@example.com
# 2. Start linking flow for Google
# 3. Log out in another tab
# 4. Complete OAuth as victim@gmail.com
# 5. Victim's Google now linked to attacker account
```

**Why this breaks:**
1. **Account takeover** - Attacker links victim's Google to attacker's account
2. **Session fixation** - OAuth state not validated against user session
3. **CSRF** - No verification that same user started and completed flow

**The fix:**

```python
# GOOD - Verify user session throughout flow
@login_required
def link_provider_view(request, provider):
    # Create cryptographically secure linking token
    token = AuthLinkingToken.objects.create(
        user=request.user,
        provider=provider,
        expires_at=timezone.now() + timedelta(minutes=15)
    )
    
    # Store token in session AND database
    request.session['linking_token'] = token.token
    request.session['linking_user_id'] = request.user.id
    
    return redirect('social:begin', backend=provider)

# users/pipeline.py
def verify_linking_token(backend, user, request, *args, **kwargs):
    """Verify user still logged in as same user who started flow"""
    token_value = request.session.get('linking_token')
    original_user_id = request.session.get('linking_user_id')
    
    if not request.user.is_authenticated:
        raise AuthException(backend, 'Must be logged in to link accounts')
    
    if request.user.id != original_user_id:
        raise AuthException(backend, 'User session changed during linking')
    
    try:
        token = AuthLinkingToken.objects.get(token=token_value)
        if not token.is_valid() or token.user_id != request.user.id:
            raise AuthException(backend, 'Invalid linking token')
        
        token.used = True
        token.save()
        return {'user': request.user}
    except AuthLinkingToken.DoesNotExist:
        raise AuthException(backend, 'Linking token not found')
```

---

### Problem: No Rate Limiting on OAuth Endpoints

```python
# BAD - Unlimited OAuth attempts
urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
]
```

**Why this breaks:**
- Attacker can spam OAuth flows to enumerate accounts
- No protection against CSRF state token brute force
- Account linking attempts not rate limited

**The fix:**

```python
# GOOD - Add rate limiting (requires django-ratelimit or similar)
from ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/h', method='GET')
def rate_limited_social_begin(request, backend):
    """Wrapper for social auth begin with rate limiting"""
    # Delegates to social_django view
    from social_django.views import auth
    return auth(request, backend)

# users/urls.py
urlpatterns = [
    path('login/<str:backend>/', rate_limited_social_begin, name='social_begin_limited'),
    path('', include('social_django.urls', namespace='social')),
]
```

---

### Problem: Not Validating OAuth State Parameter

```python
# BAD - Accepting OAuth callback without state validation
# (social_django does this by default, but custom pipelines can break it)

def custom_pipeline_step(backend, response, *args, **kwargs):
    # Directly using response without checking state
    email = response.get('email')  # WRONG - no CSRF validation
```

**Why this breaks:**
- **CSRF attacks** - Attacker can trick victim into linking attacker's Google
- **Session fixation** - State parameter not tied to user session

**The fix:**

```python
# GOOD - Let social_django handle state validation
# DO NOT bypass or override these pipeline steps:
# - 'social_core.pipeline.social_auth.social_details'
# - 'social_core.pipeline.social_auth.social_uid'
# - 'social_core.pipeline.social_auth.auth_allowed'

# Custom pipelines should run AFTER these steps
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',  # Validates state
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    
    # Safe to add custom logic here
    'users.pipeline.verify_linking_token',
    'users.pipeline.track_auth_provider',
)