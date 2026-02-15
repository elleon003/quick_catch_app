# Database Reference

## Contents
- AuthProvider Model Integration
- Query Optimization
- Migration Patterns
- Multi-Auth Tracking

---

## AuthProvider Model Integration

### Track Magic Link Usage

```python
# users/auth_models.py

from django.db import models
from django.conf import settings

class AuthProvider(models.Model):
    """
    Tracks which authentication methods a user has connected.
    Supports: email, google, linkedin, magic_link
    """
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google OAuth2'),
        ('linkedin', 'LinkedIn OAuth2'),
        ('magic_link', 'Magic Link'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auth_providers'
    )
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'provider')
        indexes = [
            models.Index(fields=['user', 'provider']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.provider}"
```

### Query User's Auth Methods

```python
# GOOD - Efficient query with select_related
from users.models import CustomUser

def get_user_auth_methods(user_id):
    """
    Returns list of authentication methods user has used.
    """
    auth_providers = AuthProvider.objects.filter(
        user_id=user_id
    ).values_list('provider', flat=True)
    
    return list(auth_providers)

# Usage in view:
def user_settings_view(request):
    methods = get_user_auth_methods(request.user.id)
    # methods = ['email', 'magic_link', 'google']
    
    context = {
        'has_password': 'email' in methods,
        'has_magic_link': 'magic_link' in methods,
        'has_google': 'google' in methods,
    }
    return render(request, 'users/settings.html', context)
```

### DON'T: N+1 Query on Auth Providers

```python
# BAD - N+1 query problem
def list_users_with_auth_methods(request):
    users = CustomUser.objects.all()
    
    user_data = []
    for user in users:
        methods = AuthProvider.objects.filter(user=user)  # ❌ Query per user
        user_data.append({
            'email': user.email,
            'methods': [m.provider for m in methods]
        })
```

**Why this breaks:**
- 1 query to fetch all users
- N queries to fetch auth providers (one per user)
- For 100 users = 101 queries

**The Fix:** Use `prefetch_related()`

```python
# GOOD - Single query with prefetch
def list_users_with_auth_methods(request):
    users = CustomUser.objects.prefetch_related('auth_providers').all()
    
    user_data = []
    for user in users:
        methods = [ap.provider for ap in user.auth_providers.all()]  # ✓ No extra queries
        user_data.append({
            'email': user.email,
            'methods': methods
        })
```

---

## Query Optimization

### Check If User Has Usable Password

```python
# GOOD - Use Django's has_usable_password()
from users.models import CustomUser

def user_needs_password_setup(user):
    """
    Returns True if user logged in via magic link/OAuth only.
    """
    return not user.has_usable_password()

# In view:
@login_required
def dashboard_view(request):
    if user_needs_password_setup(request.user):
        # User has only used magic link or OAuth
        messages.info(request, 'Set a password to enable email/password login.')
        return redirect('set_password')
    
    return render(request, 'dashboard.html')
```

### Track First-Time Magic Link Users

```python
# GOOD - Efficient query for magic-only users
from django.db.models import Q

def get_magic_only_users():
    """
    Find users who only authenticate via magic link.
    """
    return CustomUser.objects.filter(
        auth_providers__provider='magic_link'
    ).exclude(
        Q(auth_providers__provider='email') |
        Q(auth_providers__provider='google') |
        Q(auth_providers__provider='linkedin')
    ).distinct()
```

---

## Migration Patterns

### Add Magic Link Tracking to Existing Users

```python
# users/migrations/0003_populate_magic_link_providers.py

from django.db import migrations

def populate_magic_link_providers(apps, schema_editor):
    """
    Backfill AuthProvider entries for users who have logged in.
    Assumes all existing users used email/password initially.
    """
    CustomUser = apps.get_model('users', 'CustomUser')
    AuthProvider = apps.get_model('users', 'AuthProvider')
    
    users = CustomUser.objects.filter(last_login__isnull=False)
    
    auth_providers = [
        AuthProvider(user=user, provider='email')
        for user in users
        if user.has_usable_password()
    ]
    
    AuthProvider.objects.bulk_create(auth_providers, ignore_conflicts=True)

def reverse_populate(apps, schema_editor):
    """Undo the backfill."""
    AuthProvider = apps.get_model('users', 'AuthProvider')
    AuthProvider.objects.filter(provider='email').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_authprovider'),
    ]
    
    operations = [
        migrations.RunPython(populate_magic_link_providers, reverse_populate),
    ]
```

### Create AuthProvider Model Migration

```python
# users/migrations/0002_authprovider.py

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='AuthProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('provider', models.CharField(max_length=50, choices=[
                    ('email', 'Email/Password'),
                    ('google', 'Google OAuth2'),
                    ('linkedin', 'LinkedIn OAuth2'),
                    ('magic_link', 'Magic Link'),
                ])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='auth_providers',
                    to='users.customuser'
                )),
            ],
        ),
        migrations.AddIndex(
            model_name='authprovider',
            index=models.Index(fields=['user', 'provider'], name='users_authp_user_id_prov_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='authprovider',
            unique_together={('user', 'provider')},
        ),
    ]
```

---

## Multi-Auth Tracking

### Atomic Auth Provider Creation

```python
# GOOD - Thread-safe auth provider creation
from django.db import transaction
from users.models import AuthProvider

@transaction.atomic
def link_auth_provider(user, provider_name):
    """
    Safely link authentication provider to user account.
    Prevents race conditions in concurrent requests.
    """
    auth_provider, created = AuthProvider.objects.get_or_create(
        user=user,
        provider=provider_name
    )
    
    if not created:
        # Already exists, update last_used
        auth_provider.save(update_fields=['last_used'])
    
    return auth_provider
```

### Check Multiple Auth Methods

```python
# GOOD - Single query to check all methods
def get_user_auth_summary(user):
    """
    Return dict of all available auth methods for user.
    """
    providers = set(
        AuthProvider.objects.filter(user=user)
        .values_list('provider', flat=True)
    )
    
    return {
        'has_password': 'email' in providers or user.has_usable_password(),
        'has_magic_link': 'magic_link' in providers,
        'has_google': 'google' in providers,
        'has_linkedin': 'linkedin' in providers,
        'auth_method_count': len(providers),
    }

# In template:
# {% if auth_summary.auth_method_count > 1 %}
#   <p>You have {{ auth_summary.auth_method_count }} login methods</p>
# {% endif %}
```

### WARNING: Missing Indexes

```python
# BAD - No index on frequently queried field
class AuthProvider(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)
    # ❌ No index on (user, provider) lookups
```

**Why this breaks:**
- Every `AuthProvider.objects.filter(user=user)` scans full table
- Slow queries as user base grows
- Database CPU spikes under load

**The Fix:** Add composite index in Meta

```python
# GOOD - Optimized indexes
class AuthProvider(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'provider']),
        ]
        unique_together = ('user', 'provider')