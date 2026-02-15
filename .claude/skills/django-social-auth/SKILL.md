---
name: django-social-auth
description: |
  Configures OAuth2 integration for Google and LinkedIn authentication
  Use when: Setting up social login, debugging OAuth flows, managing multiple auth providers, or implementing account linking
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Django-social-auth Skill

Implements OAuth2 social authentication via `social-auth-app-django` (5.6.x). This project uses a multi-auth strategy where users can link multiple authentication methods (email/password, Google, LinkedIn, magic links) to a single account via the `AuthProvider` model.

## Quick Start

### Google OAuth2 Configuration

```python
# config/settings/base.py
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
```

### LinkedIn OAuth2 Configuration

```python
# config/settings/base.py
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = os.environ.get('LINKEDIN_CLIENT_ID')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ['emailAddress']
```

### Template Integration (DaisyUI)

```html
<!-- theme/templates/registration/login.html -->
<a href="{% url 'social:begin' 'google-oauth2' %}" 
   class="btn btn-outline gap-2">
  <svg><!-- Google icon --></svg>
  Sign in with Google
</a>

<a href="{% url 'social:begin' 'linkedin-oauth2' %}" 
   class="btn btn-outline gap-2">
  <svg><!-- LinkedIn icon --></svg>
  Sign in with LinkedIn
</a>
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| `AUTHENTICATION_BACKENDS` | Define auth methods in priority order | `('social_core.backends.google.GoogleOAuth2', 'django.contrib.auth.backends.ModelBackend')` |
| `social:begin` | Start OAuth flow | `{% url 'social:begin' 'google-oauth2' %}` |
| `social:complete` | OAuth callback URL | Automatically handled by `include('social_django.urls')` |
| `AuthProvider` model | Track linked auth methods per user | `AuthProvider.objects.filter(user=user, provider_name='google')` |
| `SOCIAL_AUTH_JSONFIELD_ENABLED` | Required for Django 3.1+ | Set to `True` in settings |

## Common Patterns

### Account Linking After Social Login

**When:** User logs in with social provider but email matches existing account

```python
# users/views.py - Custom pipeline or view
from users.models import AuthProvider

def link_social_account(backend, user, response, *args, **kwargs):
    """Link social auth to existing user account"""
    if user:
        AuthProvider.objects.get_or_create(
            user=user,
            provider_name=backend.name,
            defaults={'provider_user_id': response.get('id')}
        )
```

### Checking Connected Providers

**When:** Displaying user's connected accounts in settings

```python
# users/views.py
def user_settings_view(request):
    providers = AuthProvider.objects.filter(user=request.user)
    has_google = providers.filter(provider_name='google').exists()
    has_linkedin = providers.filter(provider_name='linkedin').exists()
    
    return render(request, 'users/auth_settings.html', {
        'has_google': has_google,
        'has_linkedin': has_linkedin,
    })
```

### Environment-Based Redirect URIs

**When:** Different callback URLs for development vs production

```python
# .env.dev
GOOGLE_REDIRECT_URI=http://localhost:8000/complete/google-oauth2/

# .env (production)
GOOGLE_REDIRECT_URI=https://yourdomain.com/complete/google-oauth2/
```

## See Also

- [routes](references/routes.md) - OAuth URL patterns and callback routing
- [services](references/services.md) - Custom pipelines and user creation logic
- [database](references/database.md) - AuthProvider model and social auth tables
- [auth](references/auth.md) - Multi-auth strategy and account linking
- [errors](references/errors.md) - OAuth errors and debugging

## Related Skills

- **django** - Core framework configuration
- **python** - Python environment and dependency management
- **postgresql** - Production database for social auth models
- **redis** - Session storage for OAuth flows
- **django-sesame** - Alternative passwordless auth method