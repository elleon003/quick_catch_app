# Errors Reference

OAuth error handling, debugging flows, and common failure scenarios.

## Contents
- OAuth Error Types
- Pipeline Error Handling
- Debugging OAuth Flows
- Provider-Specific Errors
- Anti-Patterns

---

## OAuth Error Types

### Common OAuth Errors

| Error Code | Meaning | User Action |
|------------|---------|-------------|
| `access_denied` | User declined OAuth consent | Show "Login cancelled" message |
| `invalid_client` | Wrong client ID/secret | Check environment variables |
| `redirect_uri_mismatch` | Callback URL not registered | Update OAuth provider console |
| `invalid_grant` | Authorization code expired | Retry OAuth flow |
| `invalid_scope` | Requested permission not available | Check `SOCIAL_AUTH_*_SCOPE` settings |

### Handling OAuth Errors in Views

```python
# users/views.py
from django.contrib import messages
from social_django.utils import load_backend, load_strategy

def oauth_error_view(request):
    """Handle OAuth errors gracefully"""
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')
    
    error_messages = {
        'access_denied': 'You cancelled the login process.',
        'invalid_client': 'OAuth configuration error. Please contact support.',
        'redirect_uri_mismatch': 'OAuth redirect error. Please contact support.',
        'invalid_grant': 'Login expired. Please try again.',
    }
    
    user_message = error_messages.get(
        error,
        f'Authentication error: {error_description or error}'
    )
    
    messages.error(request, user_message)
    return redirect('users:login')

# config/urls.py
urlpatterns = [
    path('users/oauth-error/', oauth_error_view, name='oauth_error'),
]

# config/settings/base.py
SOCIAL_AUTH_LOGIN_ERROR_URL = '/users/oauth-error/'
```

---

## Pipeline Error Handling

### Custom Exception Handling in Pipeline

```python
# users/pipeline.py
from social_core.exceptions import AuthException, AuthForbidden
import logging

logger = logging.getLogger(__name__)

def require_email_verified(backend, details, response, *args, **kwargs):
    """
    Require verified email from OAuth provider.
    Google: email_verified = true
    LinkedIn: email is verified by default
    """
    if backend.name == 'google-oauth2':
        email_verified = response.get('email_verified', False)
        if not email_verified:
            logger.warning(f'Unverified email from Google: {details.get("email")}')
            raise AuthForbidden(
                backend,
                'Please verify your email with Google before signing in.'
            )
    
    email = details.get('email')
    if not email:
        logger.error(f'No email from {backend.name}: {response}')
        raise AuthException(
            backend,
            'Email is required to create an account.'
        )
```

### Logging Pipeline Steps

```python
# users/pipeline.py
import logging

logger = logging.getLogger(__name__)

def log_auth_attempt(backend, details, user, *args, **kwargs):
    """Log authentication attempts for debugging"""
    logger.info(f'Auth attempt: backend={backend.name}, email={details.get("email")}, user={user}')
    
    # Log extra details in development
    if settings.DEBUG:
        logger.debug(f'OAuth response: {kwargs.get("response")}')
```

```python
# config/settings/development.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'social': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'users.pipeline': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Debugging OAuth Flows

### Enable Social Auth Debug Logging

```python
# config/settings/development.py
SOCIAL_AUTH_RAISE_EXCEPTIONS = True  # Don't silence exceptions in dev

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'social': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Debugging OAuth Callback

```bash
# Check OAuth callback URL in browser network tab
# Example: /complete/google-oauth2/?state=ABC123&code=XYZ789

# Enable Django debug toolbar for detailed request info
pip install django-debug-toolbar

# config/settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Test OAuth Flow with Test Keys

```python
# .env.dev (development only)
# Google test keys (always succeed)
GOOGLE_CLIENT_ID=test-client-id
GOOGLE_CLIENT_SECRET=test-secret

# LinkedIn test keys
LINKEDIN_CLIENT_ID=test-linkedin-id
LINKEDIN_CLIENT_SECRET=test-linkedin-secret
```

---

## Provider-Specific Errors

### Google OAuth Errors

**Error:** "redirect_uri_mismatch"

```bash
# Problem: Callback URL not registered in Google Console
# Registered: http://localhost:8000/complete/google-oauth2/
# Actual: http://127.0.0.1:8000/complete/google-oauth2/

# Fix: Add both to Google Console authorized redirect URIs:
# - http://localhost:8000/complete/google-oauth2/
# - http://127.0.0.1:8000/complete/google-oauth2/
# - https://yourdomain.com/complete/google-oauth2/
```

**Error:** "invalid_client"

```python
# Problem: Wrong client ID or secret

# Check environment variables are loaded
# config/settings/base.py
import os
print(f"Google Client ID: {os.environ.get('GOOGLE_CLIENT_ID')}")  # Debug only

# Verify .env file is loaded
from dotenv import load_dotenv
load_dotenv()  # Should be in config/settings/__init__.py
```

### LinkedIn OAuth Errors

**Error:** "insufficient_permissions"

```python
# Problem: LinkedIn app doesn't have "Sign In with LinkedIn" product

# Fix: 
# 1. Go to https://www.linkedin.com/developers/
# 2. Select your app
# 3. Go to "Products" tab
# 4. Request access to "Sign In with LinkedIn"
# 5. Wait for approval (usually instant)
```

**Error:** "invalid_scope"

```python
# Problem: Requesting LinkedIn scopes that don't exist

# BAD - r_basicprofile is deprecated
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_basicprofile', 'r_emailaddress']

# GOOD - Use current LinkedIn API v2 scopes
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ['emailAddress']
```

---

## WARNING: Error Handling Anti-Patterns

### Problem: Silencing OAuth Exceptions in Production

```python
# BAD - Hiding all errors from users
SOCIAL_AUTH_RAISE_EXCEPTIONS = False  # Don't do this!

# Result: Users see generic error, no way to debug
```

**Why this breaks:**
1. **Silent failures** - User sees "Something went wrong", no actionable info
2. **No debugging** - Can't diagnose OAuth issues in production logs
3. **Poor UX** - User doesn't know if problem is on their end or yours

**The fix:**

```python
# GOOD - Handle specific exceptions, log everything
SOCIAL_AUTH_RAISE_EXCEPTIONS = False  # Still catch exceptions

# users/pipeline.py
def handle_auth_errors(backend, details, response, *args, **kwargs):
    """Catch and log OAuth errors with context"""
    try:
        # Pipeline continues normally
        pass
    except AuthException as e:
        logger.error(f'OAuth error: backend={backend.name}, error={str(e)}, details={details}')
        
        # Show user-friendly message
        raise AuthException(
            backend,
            'Unable to complete login. Please try again or contact support.'
        )

# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    'users.pipeline.handle_auth_errors',
    'social_core.pipeline.social_auth.social_details',
    # ... rest of pipeline
)
```

---

### Problem: No Error Messages for Account Linking Failures

```python
# BAD - Linking fails silently
@login_required
def link_provider_view(request, provider):
    return redirect('social:begin', backend=provider)

# User clicks "Link Google" -> OAuth succeeds -> nothing happens -> confused user
```

**Why this breaks:**
- User doesn't know if linking succeeded
- No feedback on why linking might have failed
- Can't debug linking issues

**The fix:**

```python
# GOOD - Explicit success/failure feedback
from django.contrib import messages

# users/pipeline.py
def notify_link_success(backend, user, request, *args, **kwargs):
    """Show success message after linking provider"""
    if request.session.get('linking_token'):
        provider_names = {
            'google-oauth2': 'Google',
            'linkedin-oauth2': 'LinkedIn',
        }
        provider = provider_names.get(backend.name, backend.name)
        messages.success(request, f'{provider} account linked successfully!')
        
        # Clean up session
        del request.session['linking_token']

# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    # ... standard pipeline ...
    'users.pipeline.track_auth_provider',
    'users.pipeline.notify_link_success',  # Show success message
)
```

---

### Problem: Not Handling Duplicate Account Linking

```python
# BAD - No check if provider already linked
def link_provider_view(request, provider):
    # User already has Google linked, tries to link again
    return redirect('social:begin', backend=provider)

# Result: Creates duplicate UserSocialAuth records or crashes
```

**Why this breaks:**
- Database unique constraint violations
- Confused user: "I already linked this!"
- Wasted OAuth API calls

**The fix:**

```python
# GOOD - Check before starting OAuth flow
from social_django.models import UserSocialAuth

@login_required
def link_provider_view(request, provider):
    """Check if provider already linked before starting flow"""
    provider_map = {
        'google-oauth2': 'google-oauth2',
        'linkedin-oauth2': 'linkedin-oauth2',
    }
    backend_name = provider_map.get(provider)
    
    if UserSocialAuth.objects.filter(user=request.user, provider=backend_name).exists():
        messages.info(request, f'{provider} account is already linked.')
        return redirect('users:settings')
    
    # Create linking token
    token = AuthLinkingToken.objects.create(
        user=request.user,
        provider=backend_name,
        expires_at=timezone.now() + timedelta(minutes=15)
    )
    request.session['linking_token'] = token.token
    
    return redirect('social:begin', backend=provider)