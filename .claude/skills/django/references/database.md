# Database Reference

## Contents
- ORM Query Patterns
- Custom User Model
- N+1 Query Prevention
- Transactions
- Migrations
- Anti-Patterns

---

## ORM Query Patterns

### Querying the Custom User Model

```python
# Get user by email (primary identifier)
from users.models import CustomUser

user = CustomUser.objects.get(email='user@example.com')

# Filter active users
active_users = CustomUser.objects.filter(is_active=True)

# Check if email exists
exists = CustomUser.objects.filter(email='user@example.com').exists()

# Count users
user_count = CustomUser.objects.count()
```

**Pattern:** Use `.get()` when expecting exactly one result. Use `.filter()` for multiple results. Use `.exists()` for boolean checks (faster than `.count() > 0`).

---

## Custom User Manager

```python
# users/models.py
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hashes password
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with admin privileges."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
```

**Critical:** NEVER call `CustomUser()` directly. Always use `CustomUser.objects.create_user()` to ensure password hashing.

---

## AuthProvider Model Queries

```python
# users/auth_models.py
from users.models import AuthProvider

# Get all auth methods for a user
auth_providers = AuthProvider.objects.filter(user=user)

# Check if user has specific auth method
has_google = AuthProvider.objects.filter(
    user=user,
    provider='google'
).exists()

# Get user by social auth provider ID
try:
    auth_provider = AuthProvider.objects.get(
        provider='google',
        provider_user_id='google-user-id-12345'
    )
    user = auth_provider.user
except AuthProvider.DoesNotExist:
    user = None
```

---

## N+1 Query Prevention

### WARNING: N+1 Query Anti-Pattern

**The Problem:**

```python
# BAD - N+1 query: 1 query for users + N queries for auth_providers
users = CustomUser.objects.all()
for user in users:
    # This triggers a separate query PER USER
    providers = user.authprovider_set.all()
    print(f"{user.email} has {providers.count()} auth methods")
```

**Why This Breaks:**
1. **Performance disaster** - 101 queries for 100 users (1 + 100)
2. **Database overload** - Each query has overhead (network, parsing, execution)
3. **Scales poorly** - Doubles queries when users double

**The Fix:**

```python
# GOOD - Prefetch related auth providers in 2 queries total
users = CustomUser.objects.prefetch_related('authprovider_set').all()
for user in users:
    # No additional query - uses prefetched data
    providers = user.authprovider_set.all()
    print(f"{user.email} has {providers.count()} auth methods")
```

**When You Might Be Tempted:** Accessing related objects in loops ALWAYS triggers N+1. Use `select_related()` for ForeignKey/OneToOne, `prefetch_related()` for ManyToMany/reverse ForeignKey.

---

### Select vs Prefetch

```python
# select_related: Use for ForeignKey and OneToOne (SQL JOIN)
# Example: Get auth provider with user in 1 query
auth_provider = AuthProvider.objects.select_related('user').get(pk=1)
user = auth_provider.user  # No additional query

# prefetch_related: Use for reverse ForeignKey and ManyToMany (separate queries)
# Example: Get users with their auth providers in 2 queries
users = CustomUser.objects.prefetch_related('authprovider_set').all()
for user in users:
    providers = user.authprovider_set.all()  # No additional query
```

---

## Transactions

### Atomic Transactions

```python
from django.db import transaction

# Context manager (recommended)
with transaction.atomic():
    user = CustomUser.objects.create_user(email='user@example.com')
    AuthProvider.objects.create(user=user, provider='email')
    # If any error occurs, both operations are rolled back

# Decorator for entire view
@transaction.atomic
def register_view(request):
    # Entire view runs in a transaction
    user = CustomUser.objects.create_user(...)
    AuthProvider.objects.create(...)
    return redirect('users:dashboard')
```

**Use Cases:**
- Creating related objects (user + auth provider)
- Multi-step workflows (update user, send email, log activity)
- Bulk operations (create/update multiple records)

### Savepoints for Partial Rollbacks

```python
from django.db import transaction

with transaction.atomic():
    user = CustomUser.objects.create_user(email='user@example.com')
    
    # Create savepoint
    sid = transaction.savepoint()
    
    try:
        AuthProvider.objects.create(user=user, provider='email')
    except Exception:
        # Rollback to savepoint (user still created)
        transaction.savepoint_rollback(sid)
    else:
        # Commit savepoint
        transaction.savepoint_commit(sid)
```

**When to Use:** Rarely needed. Only use for complex workflows where partial rollback is required.

---

## Migrations

### Creating Migrations

```bash
# After model changes
python manage.py makemigrations

# Create empty migration for data migration
python manage.py makemigrations users --empty --name populate_auth_providers
```

### Data Migration Example

```python
# users/migrations/0003_populate_auth_providers.py
from django.db import migrations

def populate_auth_providers(apps, schema_editor):
    """Create AuthProvider for existing users without one."""
    CustomUser = apps.get_model('users', 'CustomUser')
    AuthProvider = apps.get_model('users', 'AuthProvider')
    
    for user in CustomUser.objects.all():
        if not AuthProvider.objects.filter(user=user, provider='email').exists():
            AuthProvider.objects.create(
                user=user,
                provider='email',
                provider_user_id=user.email
            )

def reverse_populate(apps, schema_editor):
    """Reverse migration: delete created AuthProviders."""
    AuthProvider = apps.get_model('users', 'AuthProvider')
    AuthProvider.objects.filter(provider='email').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_authprovider_authlinkingtoken'),
    ]
    
    operations = [
        migrations.RunPython(populate_auth_providers, reverse_populate),
    ]
```

**Pattern:** Data migrations use `apps.get_model()` to access historical model state. Always provide reverse operation.

---

## Database Configuration

### Split Settings Pattern

```python
# config/settings/base.py
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR.parent / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

# config/settings/development.py (override)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'db.sqlite3',
    }
}

# config/settings/production.py (override)
# Uses environment variables for PostgreSQL
```

**Pattern:** Development uses SQLite (zero config). Production uses PostgreSQL via environment variables.

---

## WARNING: Database Anti-Patterns

### Anti-Pattern 1: Unnecessary `.get()` with Exception Handling

**The Problem:**

```python
# BAD - Exception handling for expected behavior
try:
    user = CustomUser.objects.get(email=email)
except CustomUser.DoesNotExist:
    user = None
```

**Why This Breaks:**
1. **Exceptions are slow** - Exception handling has overhead
2. **Code smell** - Using exceptions for control flow is poor design
3. **Hard to read** - Try/except adds visual noise

**The Fix:**

```python
# GOOD - Use .filter().first() when existence is uncertain
user = CustomUser.objects.filter(email=email).first()  # Returns None if not found

# Or use .exists() for boolean check
if CustomUser.objects.filter(email=email).exists():
    # Do something
```

**When You Might Be Tempted:** Use `.get()` only when you expect exactly one result and want an exception if missing (e.g., in views with URLs containing PKs).

---

### Anti-Pattern 2: Using `.count()` for Existence Checks

**The Problem:**

```python
# BAD - count() fetches all matching rows
if CustomUser.objects.filter(email=email).count() > 0:
    # Do something
```

**Why This Breaks:**
1. **Slower than .exists()** - `COUNT(*)` scans all matching rows
2. **Unnecessary work** - Only need to know if ANY row exists

**The Fix:**

```python
# GOOD - exists() stops at first match
if CustomUser.objects.filter(email=email).exists():
    # Do something
```

**Performance:** `.exists()` generates `SELECT 1 FROM ... LIMIT 1` (stops immediately). `.count()` generates `SELECT COUNT(*) FROM ...` (scans all rows).

---

### Anti-Pattern 3: Forgetting Database Indexes

**The Problem:**

```python
# BAD - Querying on un-indexed field
class AuthProvider(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # No index
    provider_user_id = models.CharField(max_length=255)  # No index

# Query will do full table scan
AuthProvider.objects.filter(provider='google', provider_user_id='12345')
```

**Why This Breaks:**
1. **Slow queries** - Full table scan instead of index lookup
2. **Database load** - High CPU usage on large tables
3. **Poor scalability** - Query time grows linearly with table size

**The Fix:**

```python
# GOOD - Add composite index for frequent queries
class AuthProvider(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)
    provider_user_id = models.CharField(max_length=255)
    
    class Meta:
        indexes = [
            models.Index(fields=['provider', 'provider_user_id']),
        ]
        unique_together = [['provider', 'provider_user_id']]
```

**When You Might Be Tempted:** Add indexes on fields used in `.filter()`, `.exclude()`, or `JOIN` clauses. Monitor slow query logs.