# PostgreSQL Patterns Reference

## Contents
- Environment-Based Configuration
- Connection Management
- Schema Design Patterns
- Query Optimization Patterns
- Migration Best Practices

---

## Environment-Based Configuration

### ✅ DO: Split Settings Architecture

This project uses `config/settings/__init__.py` to load environment-specific settings:

```python
# config/settings/development.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# config/settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

**Why this works:** SQLite for fast local development (zero setup), PostgreSQL for production (matches deployment environment).

### ❌ DON'T: Hardcode Database Credentials

```python
# NEVER DO THIS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_prod_database',
        'USER': 'admin',
        'PASSWORD': 'SuperSecret123!',  # ❌ Leaked in version control
        'HOST': 'prod-db.example.com',
    }
}
```

**Why this breaks:** Credentials in source code get committed to git, exposed in logs, and visible to anyone with repo access. Use environment variables loaded from `.env` files (see `.env.docker.example`).

---

## Connection Management

### ✅ DO: Use Django's Connection Pooling (When Needed)

For high-traffic production applications, add connection pooling:

```python
# config/settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... credentials ...
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

**When to use:** Applications with >100 concurrent users. For extreme scale, use PgBouncer externally.

### ❌ DON'T: Open Manual Connections

```python
# ANTI-PATTERN
import psycopg2

def get_user_data():
    conn = psycopg2.connect(
        dbname='django_starter',
        user='postgres',
        password='...',
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users_customuser")
    # ❌ Bypasses Django ORM, breaks migrations, loses type safety
```

**Why this breaks:** Manual connections bypass Django's connection management, migration tracking, and query logging. Use Django ORM or `.raw()` queries instead.

---

## Schema Design Patterns

### ✅ DO: Email-Based Authentication (This Project's Pattern)

```python
# users/models.py (line 32)
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    # ...
    USERNAME_FIELD = 'email'
```

**PostgreSQL schema benefits:**
- `email` field has unique index (enforced at database level)
- Case-insensitive email lookups use `CITEXT` extension (if added)
- `AbstractBaseUser` generates proper foreign keys for `auth_permissions`

### ✅ DO: Track Multi-Auth with Separate Model

```python
# users/auth_models.py (line 5)
class AuthProvider(models.Model):
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google OAuth2'),
        ('linkedin', 'LinkedIn OAuth2'),
        ('magic_link', 'Magic Link'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = [['user', 'provider']]
```

**PostgreSQL features used:**
- `unique_together` creates composite index on `(user_id, provider)`
- Prevents duplicate auth methods per user
- Fast lookups: `AuthProvider.objects.filter(user=user, provider='google')`

### ❌ DON'T: Store JSON in CharField

```python
# ANTI-PATTERN
class User(models.Model):
    auth_providers = models.TextField()  # ❌ JSON string: '{"google": "...", "linkedin": "..."}'
```

**Why this breaks:**
1. Can't query: `WHERE auth_providers LIKE '%google%'` is slow and error-prone
2. No referential integrity (can't cascade delete)
3. No indexing (full table scans)
4. Race conditions when updating (must read-modify-write)

**The fix:** Use separate `AuthProvider` model with foreign key (as shown above). For true JSON columns, use `models.JSONField()` (PostgreSQL native JSON type).

---

## Query Optimization Patterns

### ✅ DO: Use select_related for Foreign Keys

```python
# users/views.py - Efficient auth provider loading
from users.auth_models import AuthProvider

def user_settings_view(request):
    # ❌ BAD - N+1 queries
    # providers = AuthProvider.objects.filter(user=request.user)
    # for p in providers:
    #     print(p.user.email)  # Triggers query per iteration
    
    # ✅ GOOD - Single JOIN query
    providers = AuthProvider.objects.filter(user=request.user).select_related('user')
```

**PostgreSQL query difference:**
- Without `select_related`: 1 query + N queries (one per auth provider)
- With `select_related`: 1 query with LEFT JOIN

### ✅ DO: Add Database Indexes for Frequent Lookups

```python
# users/models.py
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)  # Already indexed via unique=True
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)  # For range queries
```

**When to add indexes:**
- Fields in `WHERE` clauses (lookups, filters)
- Fields in `ORDER BY` (sorting)
- Foreign keys (Django auto-indexes these)
- Unique constraints (automatically indexed)

**When NOT to index:**
- Small tables (<10k rows)
- Fields that are rarely queried
- Text fields (use full-text search instead)

### ❌ DON'T: Use .count() for Existence Checks

```python
# ANTI-PATTERN
if CustomUser.objects.filter(email=email).count() > 0:  # ❌ Counts all rows
    raise ValidationError("Email exists")

# CORRECT
if CustomUser.objects.filter(email=email).exists():  # ✅ LIMIT 1 query
    raise ValidationError("Email exists")
```

**Why `.exists()` is faster:** Generates `SELECT 1 FROM ... LIMIT 1`, stops after finding first match. `.count()` scans all matching rows.

---

## Migration Best Practices

### ✅ DO: Review Generated SQL Before Applying

```bash
# After python manage.py makemigrations
python manage.py sqlmigrate users 0002

# Expected output:
BEGIN;
ALTER TABLE "users_customuser" ADD COLUMN "phone_number" varchar(20) NULL;
COMMIT;
```

**Check for:**
- `ALTER TABLE` locks (blocks writes on large tables)
- Missing indexes on new foreign keys
- Data migrations that might timeout

### ✅ DO: Use Reversible Migrations

```python
# migrations/0003_add_timezone_field.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('users', '0002_previous_migration')]
    
    operations = [
        migrations.AddField(
            model_name='customuser',
            name='timezone',
            field=models.CharField(max_length=50, default='UTC'),
        ),
    ]
```

**Reversibility:** Django auto-generates reverse operation (`RemoveField`). Test rollback with `python manage.py migrate users 0002`.

### ❌ DON'T: Modify Applied Migrations

```python
# NEVER EDIT THIS AFTER APPLYING
# migrations/0001_initial.py - Already applied in production

class Migration(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('email', models.EmailField()),  # ❌ Don't add fields here retroactively
            ],
        ),
    ]
```

**Why this breaks:** Migration hash changes, Django thinks it's unapplied, tries to recreate existing tables. **The fix:** Create new migration with `makemigrations`.