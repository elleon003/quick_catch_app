---
name: postgresql
description: |
  Manages PostgreSQL database configuration and schema for production
  Use when: Configuring database settings, writing migrations, optimizing queries, setting up production database infrastructure, or troubleshooting database performance issues
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# PostgreSQL Skill

PostgreSQL serves as the production database for this Django application, replacing SQLite in development. Configuration is environment-aware through `config/settings/production.py`, with credentials managed via environment variables. The project uses Django's ORM for schema management through migrations, with `psycopg2-binary` as the database adapter.

## Quick Start

### Production Database Configuration

```python
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

### Docker PostgreSQL Setup

```bash
# docker-compose.yml defines PostgreSQL service
docker compose up --build

# Run migrations against PostgreSQL
docker compose exec web python manage.py migrate

# Access PostgreSQL shell
docker compose exec db psql -U postgres -d django_starter
```

### Creating Database Migrations

```bash
# After modifying models in users/models.py or users/auth_models.py
python manage.py makemigrations

# Review generated migration files
python manage.py sqlmigrate users 0001

# Apply migrations
python manage.py migrate
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| **Split Settings** | Different DB per environment | SQLite (dev) vs PostgreSQL (prod) |
| **Environment Variables** | Secure credential management | `DB_NAME`, `DB_USER`, `DB_PASSWORD` |
| **psycopg2-binary** | PostgreSQL adapter for Django | Pre-compiled binary for faster install |
| **Migrations** | Version-controlled schema changes | `python manage.py makemigrations` |
| **Connection Pooling** | Not configured by default | Add `django-db-gevent` or `pgbouncer` for high traffic |

## Common Patterns

### Checking Database Connection

**When:** Debugging connection issues or validating environment configuration

```bash
# Django database shell (confirms connection works)
python manage.py dbshell

# Or use Django shell to test queries
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print(connection.get_connection_params())
```

### Backing Up Production Database

**When:** Before major migrations or deploying schema changes

```bash
# Docker environment backup
docker compose exec db pg_dump -U postgres django_starter > backup_$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T db psql -U postgres django_starter < backup_20260203.sql
```

### Optimizing Query Performance

**When:** Slow page loads or high database CPU usage

```python
# Use select_related for foreign keys (single JOIN)
user = CustomUser.objects.select_related('auth_providers').get(id=user_id)

# Use prefetch_related for reverse relations (separate queries)
users = CustomUser.objects.prefetch_related('authprovider_set').all()

# Raw SQL only when ORM can't express the query
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT ... WHERE ...")
    results = cursor.fetchall()
```

## See Also

- [patterns](references/patterns.md) - Database configuration patterns, migration strategies
- [workflows](references/workflows.md) - Migration workflow, backup procedures, production setup

## Related Skills

- **django** - Django ORM models and migrations that generate PostgreSQL schema
- **python** - Python data types map to PostgreSQL column types
- **docker** - Docker Compose orchestrates PostgreSQL service with Django
- **redis** - Often paired with PostgreSQL for caching and session storage