# Deployment Reference

## Contents
- Production Deployment Checklist
- Environment Configuration
- Static Files and Media
- Database Migrations Strategy
- Reverse Proxy Configuration
- Scaling Strategies

---

## Production Deployment Checklist

Copy this checklist for every production deployment:

```markdown
- [ ] Set environment variables:
  - [ ] `DJANGO_ENV=production`
  - [ ] `DEBUG=False`
  - [ ] `SECRET_KEY=<generate new 50-char key>`
  - [ ] `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
  - [ ] Database credentials (PostgreSQL)
  - [ ] Redis URL
  - [ ] OAuth keys (Google, LinkedIn)
  - [ ] Turnstile keys (Cloudflare)
  - [ ] SMTP settings for magic links

- [ ] Security configuration:
  - [ ] `SECURE_SSL_REDIRECT=True` (auto-enabled in production settings)
  - [ ] `SESSION_COOKIE_SECURE=True` (auto-enabled)
  - [ ] `CSRF_COOKIE_SECURE=True` (auto-enabled)
  - [ ] Update OAuth redirect URIs to production domain

- [ ] Static files:
  - [ ] Run `python manage.py tailwind build`
  - [ ] Run `python manage.py collectstatic --noinput`
  - [ ] Verify STATIC_ROOT configured correctly

- [ ] Database:
  - [ ] Run `python manage.py migrate`
  - [ ] Create superuser: `python manage.py createsuperuser`
  - [ ] Backup database before deployment

- [ ] Services:
  - [ ] Start all containers: `docker compose up -d`
  - [ ] Check health: `docker compose ps`
  - [ ] Test endpoints: `curl https://yourdomain.com/health/`
```

**Iterate until health checks pass:**
1. Deploy services
2. Run `curl -f https://yourdomain.com/health/`
3. If 500/502, check logs: `docker compose logs web`
4. Fix issues and repeat step 2
5. Only consider deployment complete when health checks pass

---

## Environment Configuration

### Production Settings (Automatic)

When `DJANGO_ENV=production`, these security features auto-enable in `config/settings/production.py`:

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database: PostgreSQL required
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
    }
}
```

**Why auto-enable?** Prevents accidental insecure deployments by enforcing HTTPS/secure cookies.

---

### DON'T: Run with DEBUG=True in production

**The Problem:**

```bash
# BAD - DEBUG mode in production
export DEBUG=True
docker compose up -d
```

**Why This Breaks:**
1. **Security risk** - Exposes stack traces with database queries, file paths
2. **Performance degradation** - Serves static files via Django (slow)
3. **Memory leaks** - Stores every SQL query in memory

**The Fix:**

```bash
# GOOD - Always DEBUG=False in production
export DJANGO_ENV=production
export DEBUG=False
docker compose up -d
```

---

## Static Files and Media

### Static Files Collection

```bash
# Development: Tailwind CSS compilation
python manage.py tailwind build

# Production: Collect all static files to STATIC_ROOT
python manage.py collectstatic --noinput
```

**Directory structure:**
```
theme/
├── static/          # Collected static files (served by Nginx/WhiteNoise)
│   └── css/
│       └── styles.css  # Compiled Tailwind CSS
└── static_src/      # Source files (not served directly)
    └── src/
        └── styles.css  # Tailwind v4 source
```

---

### Serving Static Files with Nginx

```nginx
# /etc/nginx/sites-available/myapp
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Static files served directly by Nginx
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files (user uploads)
    location /media/ {
        alias /app/media/;
        expires 7d;
    }
    
    # Proxy to Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Why Nginx for static files?** 10x faster than Django's static file serving, enables caching.

---

### Alternative: WhiteNoise for Static Files

```python
# config/settings/production.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add after SecurityMiddleware
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**When to use WhiteNoise:** Simplified deployments without Nginx (e.g., Heroku, Railway).

---

## Database Migrations Strategy

### Zero-Downtime Migrations

**The Problem:** Running migrations during deployment causes downtime.

**The Solution:** Backward-compatible migrations.

```python
# BAD - Breaking change
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField('User', 'username'),  # Breaks old code
        migrations.AddField('User', 'email', ...),
    ]
```

```python
# GOOD - Two-step migration
# Step 1: Add new field (non-breaking)
class Migration(migrations.Migration):
    operations = [
        migrations.AddField('User', 'email', null=True),  # Old code still works
    ]

# Deploy code using email field (with fallback to username)

# Step 2: Remove old field (next deployment)
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField('User', 'username'),
    ]
```

**Why two-step?** Old code continues running during deployment, no 500 errors.

---

### Migration Rollback Strategy

```bash
# List migrations
docker compose exec web python manage.py showmigrations

# Rollback last migration
docker compose exec web python manage.py migrate users 0003_previous_migration

# Rollback to beginning
docker compose exec web python manage.py migrate users zero
```

**Before rollback:** Ensure code is compatible with rolled-back schema.

---

## Reverse Proxy Configuration

### Docker Compose with Nginx

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/app/staticfiles:ro
      - ./certbot/conf:/etc/letsencrypt:ro
    depends_on:
      - web
  
  web:
    image: myapp:latest
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    expose:
      - "8000"  # Not published to host
    environment:
      - DJANGO_ENV=production
    depends_on:
      db:
        condition: service_healthy
```

**Why expose instead of ports?** Web service not accessible from outside, only via Nginx.

---

## Scaling Strategies

### Horizontal Scaling with Multiple Web Workers

```yaml
# docker-compose.prod.yml
services:
  web:
    image: myapp:latest
    deploy:
      replicas: 4  # Run 4 instances
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

```nginx
# Nginx load balancing
upstream django {
    least_conn;  # Route to least-busy worker
    server web_1:8000;
    server web_2:8000;
    server web_3:8000;
    server web_4:8000;
}
```

**Why multiple workers?** Handles concurrent requests, no single point of failure.

---

### WARNING: Session Storage with Multiple Workers

**The Problem:**

```python
# BAD - Default file-based sessions break with multiple workers
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Or file
```

**Why This Breaks:**
1. **Session affinity required** - User must hit same worker
2. **Database bottleneck** - High read/write load on DB
3. **Race conditions** - Concurrent writes to same session

**The Fix:**

```python
# GOOD - Redis-backed sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
    }
}
```

**Why Redis?** In-memory, scales horizontally, supports shared sessions across workers.

---

## See Also

- **docker** reference - Container orchestration and health checks
- **ci-cd** reference - Automated deployment pipelines
- **postgresql** skill - Database optimization and backups
- **redis** skill - Cache configuration and session storage