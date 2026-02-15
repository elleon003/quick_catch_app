# Redis Patterns Reference

## Contents
- Cache Backend Configuration
- Session Storage Patterns
- Cache Key Strategies
- Anti-Patterns and Common Mistakes
- Performance Optimization

---

## Cache Backend Configuration

### Production Redis Cache

**Current Project Pattern** (config/settings/production.py):

```python
import os

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

**Multi-Cache Configuration** (for large apps):

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',  # Different database
    },
}

SESSION_CACHE_ALIAS = 'sessions'
```

### Development vs Production Split

**DO - Environment-Specific Caching:**

```python
# config/settings/development.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': BASE_DIR / 'cache_data',
    }
}

# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
    }
}
```

**DON'T - Hardcode Redis in Base Settings:**

```python
# config/settings/base.py - BAD
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',  # Breaks dev without Redis
    }
}
```

**Why This Breaks:**
1. Forces all developers to run Redis locally
2. CI/CD pipelines fail without Redis service
3. Quick local testing becomes harder

---

## Session Storage Patterns

### Cache-Based Sessions (Production)

```python
# config/settings/production.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Fallback if cache is unavailable
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
```

**Why Use Cache-Based Sessions:**
1. **Performance** - No database hit on every request
2. **Auto-expiration** - Redis TTL handles cleanup
3. **Scalability** - Shared session store across app servers

### Session Configuration

```python
# Session timeout (1 week)
SESSION_COOKIE_AGE = 604800

# Security settings
SESSION_COOKIE_SECURE = True  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

---

## Cache Key Strategies

### Hierarchical Key Naming

**DO - Structured Keys:**

```python
from django.core.cache import cache

# Pattern: namespace:entity:id:attribute
cache_key = f"users:{user.id}:profile"
cache_key = f"posts:{post.id}:comments:count"
cache_key = f"api:v1:endpoint:{params_hash}"
```

**DON'T - Flat Unstructured Keys:**

```python
# BAD - Hard to invalidate related keys
cache_key = f"user{user.id}"
cache_key = f"{post.id}comments"
```

### Cache Key Versioning

**DO - Include Version in Keys:**

```python
CACHE_VERSION = 1  # Increment to invalidate all caches

def get_cache_key(entity, entity_id):
    return f"v{CACHE_VERSION}:{entity}:{entity_id}"

cache.set(get_cache_key('user', user_id), data)
```

### Bulk Operations

**DO - Use get_many/set_many:**

```python
# Efficient batch operations
keys = [f'user:{uid}' for uid in user_ids]
cached_users = cache.get_many(keys)

# Set multiple keys at once
cache.set_many({
    f'user:{u.id}': u.to_dict()
    for u in users
}, timeout=3600)
```

**DON'T - Loop Over get/set:**

```python
# BAD - Network round-trip for each key
for user_id in user_ids:
    data = cache.get(f'user:{user_id}')  # N network calls
```

---

## WARNING: Cache Stampede

### The Problem

```python
# BAD - Cache stampede on expiration
def get_popular_posts():
    posts = cache.get('popular_posts')
    if posts is None:
        # 1000 concurrent requests all hit this
        posts = Post.objects.filter(is_popular=True)[:10]
        cache.set('popular_posts', posts, 300)
    return posts
```

**Why This Breaks:**
1. When cache expires, ALL requests simultaneously hit the database
2. Database gets overwhelmed with identical queries
3. Response time spikes, potential timeouts

### The Fix

**Use Cache Locking:**

```python
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
import time

def get_popular_posts():
    cache_key = 'popular_posts'
    lock_key = f'{cache_key}:lock'
    
    posts = cache.get(cache_key)
    if posts is None:
        # Try to acquire lock
        if cache.add(lock_key, 'locked', timeout=10):
            try:
                posts = Post.objects.filter(is_popular=True)[:10]
                cache.set(cache_key, posts, 300)
            finally:
                cache.delete(lock_key)
        else:
            # Another process is rebuilding, wait briefly
            time.sleep(0.1)
            posts = cache.get(cache_key) or []
    
    return posts
```

**Or Use Stale-While-Revalidate:**

```python
def get_popular_posts():
    cache_key = 'popular_posts'
    stale_key = f'{cache_key}:stale'
    
    posts = cache.get(cache_key)
    if posts is None:
        # Serve stale data if available
        posts = cache.get(stale_key)
        
        # Rebuild cache asynchronously
        if cache.add(f'{cache_key}:building', 'yes', 10):
            fresh_posts = Post.objects.filter(is_popular=True)[:10]
            cache.set(cache_key, fresh_posts, 300)
            cache.set(stale_key, fresh_posts, 3600)  # Longer TTL
            posts = fresh_posts
    
    return posts or []
```

---

## WARNING: Mutable Cache Objects

### The Problem

```python
# BAD - Modifying cached objects
user_settings = cache.get(f'user:{user_id}:settings')
user_settings['theme'] = 'dark'  # Modifies cached object!
# Other processes see the change before save
```

**Why This Breaks:**
1. Redis serializes objects - changes affect the cached copy
2. Race conditions when multiple processes modify the same cached object
3. Cache becomes out of sync with database

### The Fix

**Always Create New Objects:**

```python
# GOOD - Copy before modifying
user_settings = cache.get(f'user:{user_id}:settings')
if user_settings:
    user_settings = dict(user_settings)  # Create copy
    user_settings['theme'] = 'dark'
    # Save to DB first
    user.settings = user_settings
    user.save()
    # Then update cache
    cache.set(f'user:{user_id}:settings', user_settings, 3600)
```

---

## Performance Optimization

### Connection Pooling

**Production Configuration:**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}
```

### Compression for Large Objects

```python
import pickle
import zlib
from django.core.cache import cache

def cache_large_object(key, obj, timeout=3600):
    serialized = pickle.dumps(obj)
    if len(serialized) > 1024:  # Compress if > 1KB
        compressed = zlib.compress(serialized)
        cache.set(key, compressed, timeout)
    else:
        cache.set(key, obj, timeout)
```

### Selective Caching

**DO - Cache Expensive Operations:**

```python
# Cache expensive aggregations
def get_user_statistics(user_id):
    cache_key = f'stats:user:{user_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = {
            'total_posts': Post.objects.filter(author_id=user_id).count(),
            'avg_rating': Post.objects.filter(author_id=user_id).aggregate(
                avg=Avg('rating')
            )['avg'],
        }
        cache.set(cache_key, stats, 1800)  # 30 minutes
    
    return stats
```

**DON'T - Cache Everything:**

```python
# BAD - Caching simple lookups
def get_user_email(user_id):
    cache_key = f'user:{user_id}:email'
    email = cache.get(cache_key)
    if email is None:
        email = User.objects.values_list('email', flat=True).get(id=user_id)
        cache.set(cache_key, email, 3600)
    return email
# Database indexed primary key lookup is already fast!
```

---

## Cache Invalidation Patterns

### Invalidate on Model Save

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Post)
def invalidate_post_cache(sender, instance, **kwargs):
    cache.delete(f'post:{instance.id}')
    cache.delete(f'user:{instance.author_id}:posts')
    cache.delete('popular_posts')  # Invalidate aggregates

@receiver(post_delete, sender=Post)
def invalidate_post_cache_on_delete(sender, instance, **kwargs):
    cache.delete(f'post:{instance.id}')
```

### Time-Based + Event-Based Hybrid

```python
def get_user_posts(user_id):
    cache_key = f'user:{user_id}:posts'
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = list(Post.objects.filter(author_id=user_id).values())
        # Cache for 1 hour, but invalidate on post creation
        cache.set(cache_key, posts, 3600)
    
    return posts

# Invalidate manually when post created
def create_post(author_id, title, content):
    post = Post.objects.create(author_id=author_id, title=title, content=content)
    cache.delete(f'user:{author_id}:posts')
    return post