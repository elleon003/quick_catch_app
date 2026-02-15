# Database Reference

Social auth database models, AuthProvider tracking, and data management.

## Contents
- Social Auth Default Models
- AuthProvider Custom Model
- AuthLinkingToken Model
- Query Patterns
- Anti-Patterns

---

## Social Auth Default Models

### Installed by `social-auth-app-django`

```python
# Automatically created when running migrations
# python manage.py migrate

# Tables created:
# - social_auth_usersocialauth
# - social_auth_nonce
# - social_auth_association
# - social_auth_code
```

### UserSocialAuth Model (Library-Provided)

```python
# From social_django.models import UserSocialAuth

# Fields:
# - user: ForeignKey to AUTH_USER_MODEL
# - provider: CharField (e.g., 'google-oauth2', 'linkedin-oauth2')
# - uid: CharField (provider's user ID)
# - extra_data: JSONField (OAuth response data)
# - created: DateTimeField
# - modified: DateTimeField

# Example query
from social_django.models import UserSocialAuth

# Get all social auth for user
social_auths = UserSocialAuth.objects.filter(user=request.user)

# Check if user has Google linked
has_google = UserSocialAuth.objects.filter(
    user=request.user,
    provider='google-oauth2'
).exists()

# Get OAuth extra data
google_auth = UserSocialAuth.objects.filter(
    user=request.user,
    provider='google-oauth2'
).first()

if google_auth:
    email = google_auth.extra_data.get('email')
    picture = google_auth.extra_data.get('picture')
```

---

## AuthProvider Custom Model

### Purpose: Track Authentication Methods

The `AuthProvider` model provides a cleaner abstraction over `UserSocialAuth` for this project's multi-auth strategy.

```python
# users/auth_models.py
from django.db import models
from django.conf import settings

class AuthProvider(models.Model):
    """
    Tracks which authentication providers a user has connected.
    Normalized view of authentication methods vs raw OAuth data.
    """
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
        ('linkedin', 'LinkedIn'),
        ('magic_link', 'Magic Link'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auth_providers'
    )
    provider_name = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'provider_name')
        ordering = ['-created_at']
```

### Creating AuthProvider Records

```python
# users/views.py or pipeline.py
from users.models import AuthProvider

# After email/password registration
def register_view(request):
    # ... create user ...
    
    # Track email authentication
    AuthProvider.objects.create(
        user=user,
        provider_name='email',
        provider_user_id=user.email,
    )

# After OAuth login (in custom pipeline)
def track_auth_provider(backend, user, response, *args, **kwargs):
    if user:
        provider_map = {
            'google-oauth2': 'google',
            'linkedin-oauth2': 'linkedin',
        }
        provider_name = provider_map.get(backend.name)
        
        if provider_name:
            AuthProvider.objects.update_or_create(
                user=user,
                provider_name=provider_name,
                defaults={
                    'provider_user_id': response.get('id') or response.get('sub'),
                }
            )
```

---

## AuthLinkingToken Model

### Purpose: Temporary Tokens for Account Linking

```python
# users/auth_models.py
import secrets
from django.utils import timezone

class AuthLinkingToken(models.Model):
    """
    Temporary token for linking OAuth provider to existing account.
    Prevents automatic account creation when email matches.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='linking_tokens'
    )
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    provider = models.CharField(max_length=20)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
```

### Using Linking Tokens

```python
# users/views.py
from datetime import timedelta
from django.utils import timezone
from users.models import AuthLinkingToken

@login_required
def link_provider_view(request, provider):
    """Generate token for linking provider"""
    token = AuthLinkingToken.objects.create(
        user=request.user,
        provider=provider,
        expires_at=timezone.now() + timedelta(minutes=15)
    )
    
    # Store token in session for pipeline
    request.session['linking_token'] = token.token
    
    return redirect('social:begin', backend=provider)

# users/pipeline.py
def check_linking_token(backend, user, *args, **kwargs):
    """Verify linking token in pipeline"""
    request = kwargs.get('request')
    token_value = request.session.get('linking_token')
    
    if token_value:
        try:
            token = AuthLinkingToken.objects.get(token=token_value)
            if token.is_valid() and token.provider == backend.name:
                token.used = True
                token.save()
                return {'user': token.user}  # Link to this user
        except AuthLinkingToken.DoesNotExist:
            pass
```

---

## Query Patterns

### Check User's Connected Providers

```python
# users/views.py
from users.models import AuthProvider

def user_settings_view(request):
    # Get all connected providers
    providers = AuthProvider.objects.filter(
        user=request.user,
        is_active=True
    )
    
    # Check specific providers
    has_email = providers.filter(provider_name='email').exists()
    has_google = providers.filter(provider_name='google').exists()
    has_linkedin = providers.filter(provider_name='linkedin').exists()
    has_magic_link = providers.filter(provider_name='magic_link').exists()
    
    # Count total methods
    provider_count = providers.count()
    
    # Prevent unlinking last method
    can_unlink = provider_count > 1
    
    return render(request, 'users/auth_settings.html', {
        'providers': providers,
        'has_email': has_email,
        'has_google': has_google,
        'has_linkedin': has_linkedin,
        'can_unlink': can_unlink,
    })
```

### Get OAuth Extra Data

```python
# Access provider-specific data from UserSocialAuth
from social_django.models import UserSocialAuth

def get_google_profile_picture(user):
    """Get profile picture from Google OAuth data"""
    try:
        google_auth = UserSocialAuth.objects.get(
            user=user,
            provider='google-oauth2'
        )
        return google_auth.extra_data.get('picture')
    except UserSocialAuth.DoesNotExist:
        return None

def get_linkedin_profile_url(user):
    """Get LinkedIn profile URL"""
    try:
        linkedin_auth = UserSocialAuth.objects.get(
            user=user,
            provider='linkedin-oauth2'
        )
        linkedin_id = linkedin_auth.uid
        return f"https://www.linkedin.com/in/{linkedin_id}"
    except UserSocialAuth.DoesNotExist:
        return None
```

### Unlinking Providers

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from users.models import AuthProvider
from social_django.models import UserSocialAuth

@login_required
def unlink_provider_view(request, provider):
    """Remove linked OAuth provider"""
    # Check if user has multiple auth methods
    provider_count = AuthProvider.objects.filter(
        user=request.user,
        is_active=True
    ).count()
    
    if provider_count <= 1:
        return JsonResponse({
            'error': 'Cannot unlink last authentication method'
        }, status=400)
    
    # Deactivate AuthProvider record
    AuthProvider.objects.filter(
        user=request.user,
        provider_name=provider
    ).update(is_active=False)
    
    # Delete UserSocialAuth record
    provider_map = {
        'google': 'google-oauth2',
        'linkedin': 'linkedin-oauth2',
    }
    backend_name = provider_map.get(provider)
    
    if backend_name:
        UserSocialAuth.objects.filter(
            user=request.user,
            provider=backend_name
        ).delete()
    
    return JsonResponse({'success': True})
```

---

## WARNING: Database Anti-Patterns

### Problem: Not Tracking AuthProvider in Pipeline

```python
# BAD - Only using UserSocialAuth, no abstraction layer
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    # ... standard pipeline ...
    'social_core.pipeline.user.user_details',
    # Missing: custom tracking of auth methods
)
```

**Why this breaks:**
1. **Inconsistent tracking** - Email/password users have no AuthProvider record
2. **Complex queries** - Must check multiple sources (UserSocialAuth, user.has_usable_password, sesame tokens)
3. **No unified view** - Can't easily show "you have 3 auth methods linked"

**The fix:**

```python
# GOOD - Track all auth methods uniformly
SOCIAL_AUTH_PIPELINE = (
    # ... standard pipeline ...
    'social_core.pipeline.user.user_details',
    'users.pipeline.track_auth_provider',  # Custom pipeline
)

# users/pipeline.py
def track_auth_provider(backend, user, response, *args, **kwargs):
    if user:
        provider_map = {'google-oauth2': 'google', 'linkedin-oauth2': 'linkedin'}
        provider_name = provider_map.get(backend.name)
        if provider_name:
            AuthProvider.objects.update_or_create(
                user=user,
                provider_name=provider_name,
                defaults={'provider_user_id': response.get('id') or response.get('sub')}
            )
```

---

### Problem: Deleting User Without Cascade

```python
# BAD - Orphaned social auth records remain
user = User.objects.get(email='user@example.com')
user.delete()  # UserSocialAuth and AuthProvider records remain
```

**Why this breaks:**
- Database bloat from orphaned records
- Potential PK conflicts if user re-registers with same email

**The fix:**

```python
# GOOD - Use ForeignKey with CASCADE (already done in models)
class AuthProvider(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Auto-delete when user deleted
        related_name='auth_providers'
    )