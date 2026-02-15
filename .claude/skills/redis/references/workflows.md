# Redis Workflows Reference

## Contents
- Initial Redis Setup
- Docker Redis Integration
- Production Deployment Workflow
- Monitoring and Debugging
- Cache Warming Strategies
- Troubleshooting Common Issues

---

## Initial Redis Setup

### Local Development (Optional)

Redis is NOT required for local development in this project. Development settings use file-based caching.

**If you want to test Redis locally:**

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows (WSL2 recommended)
sudo apt-get install redis-server

# Test connection
redis-cli ping
# Expected: PONG
```

### Environment Configuration

```bash
# .env (production) or .env.docker
REDIS_URL=redis://localhost:6379/1

# Docker environment
REDIS_URL=redis://redis:6379/1

# With password (production)
REDIS_URL=redis://:password@redis-host:6379/1

# Redis Sentinel (high availability)
REDIS_URL=redis-sentinel://sentinel-host:26379/mymaster/1
```

---

## Docker Redis Integration

### Add Redis to Docker Compose

**Already configured in docker-compose.yml:**

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Start Redis with Docker

```bash
# Start all services including Redis
docker compose up -d

# Check Redis health
docker compose ps redis

# View Redis logs
docker compose logs -f redis

# Connect to Redis CLI
docker compose exec redis redis-cli

# Test from Django container
docker compose exec web python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'hello')
>>> cache.get('test')
'hello'
```

---

## Production Deployment Workflow

### Checklist: Redis Production Setup

Copy this checklist and track progress:
- [ ] Step 1: Install Redis on production server or use managed service (AWS ElastiCache, Redis Cloud)
- [ ] Step 2: Configure Redis persistence (RDB snapshots or AOF)
- [ ] Step 3: Set up Redis authentication with strong password
- [ ] Step 4: Configure firewall rules (only allow Django app servers)
- [ ] Step 5: Set environment variable `REDIS_URL` in production environment
- [ ] Step 6: Verify `config/settings/production.py` uses Redis cache backend
- [ ] Step 7: Test cache connectivity before deploying Django
- [ ] Step 8: Set up monitoring (memory usage, hit rate, evictions)
- [ ] Step 9: Configure maxmemory policy (`allkeys-lru` recommended)
- [ ] Step 10: Set up automated backups if using Redis for critical data

### Production Settings Verification

```python
# config/settings/production.py - Verify these settings
import os

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
            }
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Test Cache Connectivity

```bash
# Run Django shell in production
python manage.py shell

# Test cache operations
from django.core.cache import cache
cache.set('deployment_test', 'success', 60)
print(cache.get('deployment_test'))
# Expected: 'success'

cache.delete('deployment_test')
```

### Deploy with Redis

```bash
# 1. Set environment variables
export DJANGO_ENV=production
export REDIS_URL=redis://:password@redis-host:6379/1

# 2. Install dependencies (if django-redis needed)
pip install django-redis

# 3. Run migrations
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Test cache before starting server
python manage.py shell -c "from django.core.cache import cache; cache.set('test', 1); print(cache.get('test'))"

# 6. Start application
gunicorn config.wsgi:application
```

---

## WARNING: Missing django-redis Package

**Detected:** Project's `requirements.txt` does NOT include `django-redis`

**Impact:** 
1. Production settings reference `django_redis.client.DefaultClient` but package is not installed
2. Application will crash on startup in production with `ModuleNotFoundError`
3. Advanced Redis features (connection pooling, compression) unavailable

### The Fix

**Add to requirements.txt:**

```txt
# Redis client for Django caching
django-redis==5.4.0
```

**Install package:**

```bash
pip install django-redis==5.4.0
pip freeze | grep django-redis >> requirements.txt
```

**Update Production Settings:**

```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # Use django-redis backend
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

**Why django-redis over built-in RedisCache:**
1. **Better connection pooling** - Handles connection reuse more efficiently
2. **Compression support** - Reduces memory usage for large cached objects
3. **Atomic operations** - Supports Redis-specific commands (INCR, EXPIRE, etc.)
4. **Advanced key patterns** - Wildcard deletion, pattern matching

---

## Monitoring and Debugging

### Redis CLI Monitoring

```bash
# Connect to Redis
redis-cli

# Monitor all commands in real-time
MONITOR

# Check memory usage
INFO memory

# See cache statistics
INFO stats

# List all keys (DON'T use in production with many keys)
KEYS *

# Count keys
DBSIZE

# Check specific key
GET "user:123:profile"
TTL "user:123:profile"  # Check time-to-live

# Delete specific pattern (use with caution)
redis-cli KEYS "user:*" | xargs redis-cli DEL
```

### Django Cache Debugging

```python
# management/commands/cache_stats.py
from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Test cache operations
        cache.set('debug_test', 'working', 10)
        result = cache.get('debug_test')
        
        self.stdout.write(f"Cache test: {result}")
        
        # Get cache stats (if using django-redis)
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection('default')
            info = redis_conn.info()
            
            self.stdout.write(f"Redis version: {info['redis_version']}")
            self.stdout.write(f"Connected clients: {info['connected_clients']}")
            self.stdout.write(f"Used memory: {info['used_memory_human']}")
            self.stdout.write(f"Total keys: {redis_conn.dbsize()}")
        except ImportError:
            self.stdout.write("django-redis not installed")
```

**Run cache statistics:**

```bash
python manage.py cache_stats
```

### Monitor Cache Hit Rate

```python
# Middleware to log cache performance
class CacheMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.core.cache import cache
        
        # Track cache hits/misses
        cache.add('cache_hits', 0)
        cache.add('cache_misses', 0)
        
        response = self.get_response(request)
        return response
```

---

## Cache Warming Strategies

### Warm Cache on Deployment

```python
# management/commands/warm_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
from users.models import CustomUser
from myapp.models import Post

class Command(BaseCommand):
    help = "Warm cache with frequently accessed data"

    def handle(self, *args, **options):
        # Cache popular posts
        popular_posts = Post.objects.filter(is_popular=True)[:10]
        cache.set('popular_posts', list(popular_posts.values()), 3600)
        self.stdout.write(f"Cached {popular_posts.count()} popular posts")
        
        # Cache active users
        active_users = CustomUser.objects.filter(is_active=True)
        for user in active_users[:100]:  # Top 100 active users
            cache.set(f'user:{user.id}:profile', {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }, 3600)
        
        self.stdout.write(f"Cache warmed successfully")
```

**Run after deployment:**

```bash
python manage.py warm_cache
```

### Scheduled Cache Warming

**Use celery or cron to refresh cache periodically:**

```python
# tasks.py (if using Celery)
from celery import shared_task
from django.core.cache import cache

@shared_task
def refresh_popular_posts():
    posts = Post.objects.filter(is_popular=True)[:10]
    cache.set('popular_posts', list(posts.values()), 3600)
    return f"Refreshed {posts.count()} posts"

# Schedule every 15 minutes
```

---

## Troubleshooting Common Issues

### Issue: Connection Refused

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Debug Steps:**

1. Check if Redis is running:
   ```bash
   # Local
   redis-cli ping
   
   # Docker
   docker compose ps redis
   docker compose logs redis
   ```

2. Verify connection URL:
   ```bash
   echo $REDIS_URL
   # Should match Redis host and port
   ```

3. Test network connectivity:
   ```bash
   # From Django container to Redis
   docker compose exec web ping redis
   telnet redis 6379
   ```

4. Check firewall rules (production):
   ```bash
   # Allow Redis port
   sudo ufw allow 6379
   ```

### Issue: Cache Not Persisting

**Symptoms:**
- Cache data disappears after Redis restart
- Session data lost

**Debug Steps:**

1. Check Redis persistence configuration:
   ```bash
   redis-cli CONFIG GET save
   redis-cli CONFIG GET appendonly
   ```

2. Enable persistence:
   ```bash
   # docker-compose.yml
   command: redis-server --appendonly yes --save 60 1000
   ```

3. Verify data directory:
   ```bash
   docker compose exec redis ls -la /data
   ```

### Issue: High Memory Usage

**Symptoms:**
- Redis memory continuously growing
- Out of memory errors

**Debug Steps:**

1. Check memory usage:
   ```bash
   redis-cli INFO memory
   ```

2. Set maxmemory policy:
   ```bash
   # docker-compose.yml
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

3. Identify large keys:
   ```bash
   redis-cli --bigkeys
   ```

4. Review cache TTLs:
   ```python
   # Ensure all cached data has expiration
   cache.set(key, value, timeout=3600)  # Always set timeout
   ```

### Issue: Stale Cache Data

**Symptoms:**
- Users see outdated information
- Changes not reflected immediately

**Debug Steps:**

1. Verify cache invalidation on model save:
   ```python
   @receiver(post_save, sender=Post)
   def invalidate_cache(sender, instance, **kwargs):
       cache.delete(f'post:{instance.id}')
   ```

2. Check cache key consistency:
   ```python
   # Ensure same key format everywhere
   CACHE_KEY_FORMAT = 'user:{user_id}:profile'
   ```

3. Manually flush specific keys:
   ```bash
   redis-cli KEYS "user:*" | xargs redis-cli DEL
   ```

4. Full cache clear (last resort):
   ```bash
   redis-cli FLUSHDB
   # Or from Django
   python manage.py shell -c "from django.core.cache import cache; cache.clear()"
   ```

---

## Performance Testing

### Benchmark Cache Operations

```python
import time
from django.core.cache import cache

def benchmark_cache():
    # Write performance
    start = time.time()
    for i in range(1000):
        cache.set(f'bench:{i}', {'data': 'x' * 100}, 300)
    write_time = time.time() - start
    
    # Read performance
    start = time.time()
    for i in range(1000):
        cache.get(f'bench:{i}')
    read_time = time.time() - start
    
    print(f"Write 1000 keys: {write_time:.2f}s")
    print(f"Read 1000 keys: {read_time:.2f}s")
    
    # Cleanup
    for i in range(1000):
        cache.delete(f'bench:{i}')
```

### Monitor Production Cache

**Use Redis slow log:**

```bash
# Set slow log threshold to 10ms
redis-cli CONFIG SET slowlog-log-slower-than 10000

# View slow queries
redis-cli SLOWLOG GET 10