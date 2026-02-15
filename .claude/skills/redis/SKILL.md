---
name: redis
description: |
  Configures Redis caching, session storage, and queue management
  Use when: Setting up caching layers, session backends, or task queues in Django production environments
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Redis Skill

Redis provides high-performance in-memory caching and session storage for Django applications. This project uses Redis in production (`config/settings/production.py`) for both cache backend and session storage, while development uses file-based caching and database sessions.

## Quick Start

### Production Cache Configuration

```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
```

### Session Storage with Redis

```python
# config/settings/production.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Docker Redis Service

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| Cache Backend | Store computed results, reduce DB load | `cache.set('key', value, 300)` |
| Session Storage | Store user session data in-memory | `SESSION_ENGINE = 'cache'` |
| Connection URL | Configure Redis host/port/database | `redis://localhost:6379/1` |
| Cache Alias | Multiple cache configurations | `CACHE_ALIAS = 'default'` |
| TTL | Time-to-live for cached data | `cache.set(key, val, timeout=3600)` |

## Common Patterns

### View-Level Caching

**When:** Cache expensive computations or database queries

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def expensive_view(request):
    return render(request, 'template.html')
```

### Fragment Caching in Templates

**When:** Cache parts of a template that are expensive to render

```django
{% load cache %}
{% cache 500 sidebar request.user.username %}
    .. expensive sidebar ..
{% endcache %}
```

### Manual Cache Operations

**When:** Custom caching logic with conditional invalidation

```python
from django.core.cache import cache

# Get or compute
user_data = cache.get(f'user:{user_id}')
if user_data is None:
    user_data = expensive_computation(user_id)
    cache.set(f'user:{user_id}', user_data, timeout=3600)

# Delete on update
cache.delete(f'user:{user_id}')
```

## Environment Configuration

```bash
# .env or .env.docker
REDIS_URL=redis://localhost:6379/1

# Docker environment
REDIS_URL=redis://redis:6379/1
```

## See Also

- [patterns](references/patterns.md) - Caching strategies and Redis patterns
- [workflows](references/workflows.md) - Setup workflows and troubleshooting

## Related Skills

- **django** - Django framework configuration and settings
- **python** - Python Redis client usage
- **docker** - Running Redis in containers
- **postgresql** - Database that Redis complements for caching