# PostgreSQL Workflows Reference

## Contents
- Initial Production Setup
- Migration Workflow
- Backup and Restore
- Performance Troubleshooting
- Production Deployment Checklist

---

## Initial Production Setup

### Setting Up PostgreSQL for Production

**Copy this checklist and track progress:**

```markdown
- [ ] Create PostgreSQL database and user
- [ ] Configure environment variables
- [ ] Test database connection
- [ ] Run initial migrations
- [ ] Create superuser
- [ ] Verify authentication works
```

**Step 1: Create Database and User**

```bash
# On production server or Docker
docker compose exec db psql -U postgres

# Inside PostgreSQL shell:
CREATE DATABASE django_starter;
CREATE USER django_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE django_starter TO django_user;

# PostgreSQL 15+ requires additional grant for public schema
\c django_starter
GRANT ALL ON SCHEMA public TO django_user;
```

**Step 2: Configure Environment Variables**

```bash
# .env (production) or .env.docker (Docker)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=django_starter
DB_USER=django_user
DB_PASSWORD=strong_password_here
DB_HOST=db  # 'localhost' if not using Docker
DB_PORT=5432
DJANGO_ENV=production
```

**Step 3: Test Connection**

```bash
# Verify Django can connect
python manage.py check --database default

# Expected output:
# System check identified no issues (0 silenced).

# Open database shell to confirm
python manage.py dbshell
\dt  # List tables (should be empty before migrations)
\q   # Quit
```

**Step 4: Run Migrations**

```bash
# Apply all migrations
python manage.py migrate

# Verify tables created
python manage.py dbshell
\dt  # Should show: users_customuser, users_authprovider, auth_*, django_*, social_auth_*
```

**Step 5: Create Superuser**

```bash
python manage.py createsuperuser
# Email: admin@example.com
# Password: (enter secure password)
```

---

## Migration Workflow

### Creating and Applying Model Changes

**Standard workflow:**

```bash
# 1. Modify models (e.g., users/models.py)
# Example: Add phone_number field to CustomUser

# 2. Generate migration
python manage.py makemigrations

# Expected output:
# Migrations for 'users':
#   users/migrations/0003_customuser_phone_number.py
#     - Add field phone_number to customuser

# 3. Review generated SQL
python manage.py sqlmigrate users 0003

# 4. Check for issues before applying
python manage.py migrate --plan

# 5. Apply migration
python manage.py migrate

# 6. Verify in database
python manage.py dbshell
\d users_customuser  # Describe table, confirm new column exists
```

### Data Migrations for Complex Changes

**When:** Populating default values, transforming existing data, or multi-step schema changes.

```python
# migrations/0004_populate_timezone.py
from django.db import migrations

def populate_timezones(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    # Bulk update (efficient for large datasets)
    CustomUser.objects.filter(timezone__isnull=True).update(timezone='UTC')

class Migration(migrations.Migration):
    dependencies = [('users', '0003_add_timezone_field')]
    
    operations = [
        migrations.RunPython(populate_timezones, migrations.RunPython.noop),
    ]
```

**Validation loop:**

1. Apply migration: `python manage.py migrate`
2. Validate data: `python manage.py shell`
   ```python
   from users.models import CustomUser
   assert not CustomUser.objects.filter(timezone__isnull=True).exists()
   ```
3. If validation fails, rollback: `python manage.py migrate users 0003`
4. Fix data migration code and repeat

---

## Backup and Restore

### Backup Workflows

**Before Major Deployments:**

```bash
# Docker environment
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec db pg_dump -U postgres -Fc django_starter > "$BACKUP_FILE"

# Verify backup integrity
pg_restore --list "$BACKUP_FILE" | head -n 20
```

**Automated Daily Backups (Production):**

```bash
# Add to cron: 0 2 * * * /path/to/backup_script.sh

#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
BACKUP_FILE="$BACKUP_DIR/django_starter_$(date +%Y%m%d).sql.gz"

pg_dump -U django_user -h localhost django_starter | gzip > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "django_starter_*.sql.gz" -mtime +7 -delete
```

### Restore Workflows

**Restoring from Backup:**

```bash
# 1. Stop Django application to prevent writes
docker compose stop web

# 2. Drop and recreate database (DESTRUCTIVE)
docker compose exec db psql -U postgres -c "DROP DATABASE django_starter;"
docker compose exec db psql -U postgres -c "CREATE DATABASE django_starter;"

# 3. Restore from backup
docker compose exec -T db pg_restore -U postgres -d django_starter < backup_20260203.sql

# 4. Restart application
docker compose start web
```

**Validation after restore:**

```bash
# Check row counts match expected
docker compose exec web python manage.py shell
>>> from users.models import CustomUser
>>> CustomUser.objects.count()  # Compare with pre-restore count
>>> from users.auth_models import AuthProvider
>>> AuthProvider.objects.count()
```

---

## Performance Troubleshooting

### Diagnosing Slow Queries

**Step 1: Enable Query Logging**

```python
# config/settings/development.py (temporary, for debugging)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**Step 2: Identify Slow Queries**

```bash
# PostgreSQL slow query log (enable in postgresql.conf)
# log_min_duration_statement = 1000  # Log queries >1 second

# View logs
docker compose logs db | grep "duration:"

# Example output:
# duration: 2341.123 ms  statement: SELECT * FROM users_customuser WHERE email LIKE '%@gmail.com'
```

**Step 3: Analyze with EXPLAIN**

```sql
-- In psql shell
EXPLAIN ANALYZE SELECT * FROM users_customuser WHERE email LIKE '%@gmail.com';

-- Look for:
-- Seq Scan (bad - full table scan)
-- Index Scan (good - uses index)
-- High cost numbers
```

**Step 4: Add Indexes**

```python
# users/models.py
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)  # Already indexed
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)  # Add index

# Generate migration
python manage.py makemigrations
python manage.py migrate
```

### Optimizing N+1 Query Problems

**Debugging process:**

```python
# Install django-debug-toolbar (dev only)
# pip install django-debug-toolbar

# In views.py - check query count
from django.db import connection
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def user_settings_view(request):
    providers = AuthProvider.objects.filter(user=request.user)
    
    # Print queries executed
    for query in connection.queries:
        print(query['sql'])
    
    # ❌ BAD: Shows multiple SELECT queries
    # SELECT * FROM users_authprovider WHERE user_id = 1
    # SELECT * FROM users_customuser WHERE id = 1  (repeated for each provider)
```

**Fix with select_related:**

```python
# ✅ GOOD: Single JOIN query
providers = AuthProvider.objects.filter(user=request.user).select_related('user')

# Verify with EXPLAIN
print(providers.query)
# SELECT ... FROM users_authprovider INNER JOIN users_customuser ON (...)
```

---

## Production Deployment Checklist

**Pre-Deployment:**

```markdown
- [ ] Backup production database
- [ ] Test migrations on staging database (copy of production)
- [ ] Review migration SQL for locking operations
- [ ] Check for indexes on new foreign keys
- [ ] Estimate migration time (test on production-sized dataset)
- [ ] Plan maintenance window if migration locks tables
```

**Deployment:**

```bash
# 1. Pull latest code
git pull origin main

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install updated dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate --no-input

# 5. Collect static files (if changed)
python manage.py collectstatic --no-input

# 6. Restart application server
# systemctl restart gunicorn  (or equivalent)
# docker compose restart web  (Docker)
```

**Post-Deployment Validation:**

```bash
# Check migration status
python manage.py showmigrations | grep "\[ \]"  # Should be empty

# Smoke test database queries
python manage.py check

# Test user login flow
curl -I https://yourdomain.com/users/login/  # Should return 200

# Monitor error logs
tail -f /var/log/django/error.log
# docker compose logs -f web  (Docker)
```

**Rollback Procedure (If Deployment Fails):**

```bash
# 1. Revert code
git revert HEAD
git push origin main

# 2. Rollback migrations (if applied)
python manage.py migrate users 0002  # Previous migration number

# 3. Restore database backup (last resort)
# See "Restore Workflows" section above

# 4. Restart application
docker compose restart web