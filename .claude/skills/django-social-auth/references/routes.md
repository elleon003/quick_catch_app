# Routes Reference

URL patterns for OAuth2 flows, callbacks, and account linking.

## Contents
- OAuth Provider URLs
- Callback Routing
- Account Linking Flows
- Anti-Patterns
- Debugging OAuth Redirects

---

## OAuth Provider URLs

### Standard Social Auth URLs

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    # Social auth URLs (handles both initiation and callbacks)
    path('', include('social_django.urls', namespace='social')),
    
    # Your custom auth URLs
    path('users/', include('users.urls')),
]
```

**Generated URL patterns:**
- `/login/google-oauth2/` - Initiate Google OAuth
- `/login/linkedin-oauth2/` - Initiate LinkedIn OAuth
- `/complete/google-oauth2/` - Google callback
- `/complete/linkedin-oauth2/` - LinkedIn callback

### Template URL References

```html
<!-- theme/templates/registration/login.html -->
{% load static %}

<!-- GOOD - Use named URL patterns -->
<a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.GET.next|urlencode }}">
  Sign in with Google
</a>

<!-- BAD - Hardcoded URLs break when routes change -->
<a href="/login/google-oauth2/">
  Sign in with Google
</a>
```

**Why named URLs matter:**
- Routes centralized in `social_django.urls`
- Library updates don't break templates
- `next` parameter preserves redirect destination

---

## Callback Routing

### OAuth2 Callback Flow

```python
# Automatic by social_django - NO manual view needed
# /complete/google-oauth2/ -> social_core.backends.google.GoogleOAuth2

# config/settings/base.py
SOCIAL_AUTH_URL_NAMESPACE = 'social'  # Default namespace

# Redirect after successful authentication
LOGIN_REDIRECT_URL = '/users/dashboard/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/users/dashboard/'

# Redirect after error
LOGIN_ERROR_URL = '/users/login/?error=social_auth'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/users/login/?error=social_auth'
```

### Custom Post-Login Redirect

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def post_social_login(request):
    """Custom logic after social login"""
    if not request.user.first_name:
        # Redirect to profile completion if missing data
        return redirect('users:complete_profile')
    return redirect('users:dashboard')

# config/urls.py
urlpatterns = [
    path('users/post-login/', post_social_login, name='post_social_login'),
]

# config/settings/base.py
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/users/post-login/'
```

---

## Account Linking Flows

### Linking Additional Providers to Existing Account

```python
# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('settings/', views.user_settings_view, name='settings'),
    path('link/<str:provider>/', views.link_provider_view, name='link_provider'),
    path('unlink/<str:provider>/', views.unlink_provider_view, name='unlink_provider'),
]
```

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

@login_required
def link_provider_view(request, provider):
    """Initiate OAuth flow to link additional provider"""
    if provider not in ['google-oauth2', 'linkedin-oauth2']:
        return redirect('users:settings')
    
    # Store intent to link (not create new user)
    request.session['link_provider'] = True
    
    # Redirect to social auth
    return redirect(f'social:begin', backend=provider)
```

### Template for Account Linking

```html
<!-- theme/templates/users/auth_settings.html -->
{% if not has_google %}
<a href="{% url 'users:link_provider' 'google-oauth2' %}" 
   class="btn btn-primary">
  Link Google Account
</a>
{% else %}
<button class="btn btn-outline btn-error"
        hx-post="{% url 'users:unlink_provider' 'google-oauth2' %}"
        hx-confirm="Unlink Google account?">
  Unlink Google
</button>
{% endif %}
```

---

## WARNING: Common Routing Anti-Patterns

### Problem: Hardcoded OAuth Redirect URIs

```python
# BAD - Hardcoded callback URL
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://localhost:8000/complete/google-oauth2/'
```

**Why this breaks:**
1. **Production fails** - localhost URL doesn't work on production domain
2. **HTTPS mismatch** - Local HTTP vs production HTTPS causes OAuth errors
3. **Port changes** - Different dev ports (8000, 8080) break callbacks

**The fix:**

```python
# GOOD - Let Django generate callback URLs automatically
# No SOCIAL_AUTH_*_REDIRECT_URI setting needed

# Django constructs: {scheme}://{host}/complete/{provider}/
# Development: http://localhost:8000/complete/google-oauth2/
# Production: https://yourdomain.com/complete/google-oauth2/
```

**Configure in OAuth provider console instead:**
- Google Console: Add both `http://localhost:8000/complete/google-oauth2/` AND `https://yourdomain.com/complete/google-oauth2/`
- LinkedIn Portal: Same pattern

---

### Problem: Missing `next` Parameter Handling

```python
# BAD - User loses intended destination after login
<a href="{% url 'social:begin' 'google-oauth2' %}">
  Sign in with Google
</a>
```

**Why this breaks:**
- User clicks "View Dashboard" → redirected to login → logs in → sent to default URL instead of dashboard

**The fix:**

```html
<!-- GOOD - Preserve redirect destination -->
<a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.GET.next|urlencode }}">
  Sign in with Google
</a>
```

```python
# config/settings/base.py
# Respect ?next parameter after login
SOCIAL_AUTH_SANITIZE_REDIRECTS = False  # If you trust your next URLs
SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = ['/users/dashboard/', '/users/settings/']
```

---

## Debugging OAuth Redirects

### Enable Social Auth Logging

```python
# config/settings/development.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'social': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Test OAuth Flow Manually

```bash
# 1. Start OAuth flow
curl -I http://localhost:8000/login/google-oauth2/

# Look for Location header with OAuth URL

# 2. Check callback handling
# After OAuth consent, check server logs for:
# - "Received OAuth callback"
# - "User authenticated: user@example.com"
# - "Redirecting to /users/dashboard/"