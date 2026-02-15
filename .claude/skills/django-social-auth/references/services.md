# Services Reference

Custom pipelines, user creation logic, and social auth backend customization.

## Contents
- Custom Pipeline Functions
- User Association Logic
- Profile Data Extraction
- Anti-Patterns
- Email Verification

---

## Custom Pipeline Functions

### Default Social Auth Pipeline

```python
# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    # Get social auth details from provider
    'social_core.pipeline.social_auth.social_details',
    
    # Get user ID from social network
    'social_core.pipeline.social_auth.social_uid',
    
    # Check if current user is authenticated and associate
    'social_core.pipeline.social_auth.auth_allowed',
    
    # Create social auth record or get existing one
    'social_core.pipeline.social_auth.social_user',
    
    # Get user by email if social account not yet associated
    'social_core.pipeline.user.get_username',
    
    # Create new user if no match found
    'social_core.pipeline.user.create_user',
    
    # Associate current user with social account
    'social_core.pipeline.social_auth.associate_user',
    
    # Load extra data from provider
    'social_core.pipeline.social_auth.load_extra_data',
    
    # Update user record with social data
    'social_core.pipeline.user.user_details',
)
```

### Custom Pipeline: Track Auth Provider

```python
# users/pipeline.py
from users.models import AuthProvider

def track_auth_provider(backend, user, response, *args, **kwargs):
    """
    Create or update AuthProvider record after social auth.
    Runs AFTER user creation/association.
    """
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
                    'is_active': True,
                }
            )
```

```python
# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    
    # CUSTOM: Track authentication provider
    'users.pipeline.track_auth_provider',
)
```

---

## User Association Logic

### Associate Social Account to Existing User by Email

```python
# users/pipeline.py
from django.contrib.auth import get_user_model

User = get_user_model()

def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate social account with existing user if email matches.
    Place BEFORE create_user in pipeline to prevent duplicates.
    """
    if user:
        return None  # Already authenticated
    
    email = details.get('email')
    if not email:
        return None  # Can't associate without email
    
    try:
        existing_user = User.objects.get(email=email)
        return {
            'user': existing_user,
            'is_new': False,
        }
    except User.DoesNotExist:
        return None  # Will proceed to create_user step
```

```python
# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    
    # CUSTOM: Link to existing user by email BEFORE creating new user
    'users.pipeline.associate_by_email',
    
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'users.pipeline.track_auth_provider',
)
```

### Prevent Duplicate User Creation

```python
# users/pipeline.py
def prevent_duplicate_by_email(backend, details, user=None, *args, **kwargs):
    """
    STOP pipeline if user with email exists but isn't linked.
    Use for requiring manual account linking.
    """
    if user:
        return None
    
    email = details.get('email')
    if email and User.objects.filter(email=email).exists():
        # Redirect to account linking page
        raise AuthException(
            backend,
            'An account with this email already exists. Please log in first.'
        )
```

---

## Profile Data Extraction

### Extract Profile Data from Google OAuth

```python
# users/pipeline.py
def extract_google_profile(backend, details, response, user=None, *args, **kwargs):
    """
    Extract profile data from Google OAuth response.
    Google returns: sub, email, name, given_name, family_name, picture
    """
    if backend.name != 'google-oauth2' or not user:
        return None
    
    updated = False
    
    # Update first/last name if missing
    if not user.first_name and response.get('given_name'):
        user.first_name = response['given_name']
        updated = True
    
    if not user.last_name and response.get('family_name'):
        user.last_name = response['family_name']
        updated = True
    
    # Store profile picture URL in user model or profile
    if response.get('picture'):
        # Assuming you have a profile_picture field
        # user.profile_picture = response['picture']
        pass
    
    if updated:
        user.save()
```

### Extract Profile Data from LinkedIn OAuth

```python
# users/pipeline.py
def extract_linkedin_profile(backend, details, response, user=None, *args, **kwargs):
    """
    Extract profile data from LinkedIn OAuth response.
    LinkedIn returns: id, firstName, lastName, profilePicture, emailAddress
    """
    if backend.name != 'linkedin-oauth2' or not user:
        return None
    
    updated = False
    
    # LinkedIn v2 API returns localizedFirstName/localizedLastName
    if not user.first_name and response.get('localizedFirstName'):
        user.first_name = response['localizedFirstName']
        updated = True
    
    if not user.last_name and response.get('localizedLastName'):
        user.last_name = response['localizedLastName']
        updated = True
    
    if updated:
        user.save()
```

```python
# config/settings/base.py
SOCIAL_AUTH_PIPELINE = (
    # ... standard pipeline steps ...
    'social_core.pipeline.user.user_details',
    
    # CUSTOM: Extract provider-specific profile data
    'users.pipeline.extract_google_profile',
    'users.pipeline.extract_linkedin_profile',
    'users.pipeline.track_auth_provider',
)
```

---

## WARNING: Pipeline Anti-Patterns

### Problem: Modifying User in Wrong Pipeline Order

```python
# BAD - Trying to update user before it's created
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'users.pipeline.extract_google_profile',  # WRONG - user doesn't exist yet
    'social_core.pipeline.user.create_user',
    # ...
)
```

**Why this breaks:**
1. **NoneType errors** - `user` parameter is None before `create_user` step
2. **Data loss** - Profile extraction runs before user exists, data discarded
3. **Pipeline crashes** - Accessing `user.first_name` when `user is None`

**The fix:**

```python
# GOOD - Update user AFTER creation and association
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',  # User created here
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    
    # GOOD - Custom pipelines run AFTER user exists
    'users.pipeline.extract_google_profile',
    'users.pipeline.track_auth_provider',
)
```

---

### Problem: Creating Multiple Users for Same Email

```python
# BAD - No email association, creates duplicate users
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',  # Creates new user every time
    # ...
)
```

**Why this breaks:**
- User registers with email/password: `user1@example.com`
- User logs in with Google (same email): creates `user2@example.com`
- Now two accounts exist, data fragmented

**The fix:**

```python
# GOOD - Associate by email before creating
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    
    # Check if email exists before creating new user
    'users.pipeline.associate_by_email',
    
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',  # Only runs if no match found
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'users.pipeline.track_auth_provider',
)
```

---

## Email Verification

### Require Email Verification Before Account Creation

```python
# config/settings/base.py
# Require verified email from OAuth providers
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'prompt': 'select_account',  # Always show account picker
}

# Verify email is present in OAuth response
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']  # Don't overwrite if exists
```

```python
# users/pipeline.py
def require_email(backend, details, user=None, *args, **kwargs):
    """Require email from OAuth provider"""
    email = details.get('email')
    if not email:
        raise AuthException(
            backend,
            'Email is required to create an account.'
        )