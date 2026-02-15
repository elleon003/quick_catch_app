# Python Patterns Reference

## Contents
- Idiomatic Python Patterns
- Django-Specific Patterns
- Error Handling Conventions
- Async Patterns
- Memory and Performance

---

## Idiomatic Python Patterns

### List Comprehensions Over map/filter

```python
# GOOD - Pythonic and readable
active_users = [u for u in users if u.is_active]
emails = [u.email for u in users]

# AVOID - Less readable in Python
active_users = list(filter(lambda u: u.is_active, users))
emails = list(map(lambda u: u.email, users))
```

**Why:** List comprehensions are more Pythonic, easier to read, and often faster.

### Context Managers for Resource Management

```python
# GOOD - Automatic cleanup
with open('file.txt', 'r') as f:
    data = f.read()
# File automatically closed

# BAD - Manual cleanup (error-prone)
f = open('file.txt', 'r')
data = f.read()
f.close()  # Might not execute if exception occurs
```

**Why:** Context managers guarantee cleanup even if exceptions occur.

### Dictionary .get() with Defaults

```python
# GOOD - Safe with default
user_role = user_data.get('role', 'guest')

# AVOID - Risk of KeyError
try:
    user_role = user_data['role']
except KeyError:
    user_role = 'guest'
```

**Why:** `.get()` is concise and avoids exception handling for missing keys.

### Pathlib Over os.path

```python
from pathlib import Path

# GOOD - Modern and cross-platform
BASE_DIR = Path(__file__).resolve().parent.parent
config_file = BASE_DIR / 'config' / 'settings.py'

# LEGACY - Verbose and platform-specific
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_file = os.path.join(BASE_DIR, 'config', 'settings.py')
```

**Why:** Pathlib is object-oriented, chainable, and handles cross-platform paths automatically.

---

## Django-Specific Patterns

### Model Managers for Reusable Queries

```python
# users/models.py
from django.db import models

class CustomUserManager(models.Manager):
    def create_user(self, email, password=None, **extra_fields):
        """Centralized user creation logic"""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def active_users(self):
        """Reusable query for active users"""
        return self.filter(is_active=True)

class CustomUser(models.Model):
    email = models.EmailField(unique=True)
    objects = CustomUserManager()
```

**Why:** Managers keep query logic DRY and testable. Every app can reuse `CustomUser.objects.active_users()`.

### WARNING: Mutable Default Arguments

**The Problem:**

```python
# BAD - Default list is shared across all calls
def add_provider(user, providers=[]):
    providers.append(user.provider)
    return providers

# First call: ['google']
# Second call: ['google', 'linkedin']  # BUG: Previous value persists!
```

**Why This Breaks:**
1. Python evaluates default arguments once at function definition, not per call
2. Mutable objects (list, dict) are shared across all invocations
3. Causes data corruption and hard-to-debug state bugs

**The Fix:**

```python
# GOOD - Create new list per call
def add_provider(user, providers=None):
    if providers is None:
        providers = []
    providers.append(user.provider)
    return providers
```

**When You Might Be Tempted:** Default empty lists seem convenient, but they're a Python footgun.

### View Function Patterns

```python
# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def user_settings_view(request):
    """User settings page with form handling"""
    if request.method == 'POST':
        # Process form
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated')
            return redirect('user_settings')
    else:
        # Display form
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'user_settings.html', {'form': form})
```

**Why:** Standard Django pattern: POST for mutations, GET for display. Redirect after POST prevents form resubmission.

### QuerySet select_related/prefetch_related

```python
# GOOD - Single query with JOIN
users = CustomUser.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional query

# GOOD - Batch query for many-to-many
users = CustomUser.objects.prefetch_related('auth_providers').all()
for user in users:
    print(user.auth_providers.count())  # No N+1 queries

# BAD - N+1 queries (one per user)
users = CustomUser.objects.all()
for user in users:
    print(user.profile.bio)  # Triggers query for each user
```

**Why:** `select_related` (ForeignKey/OneToOne) uses SQL JOINs. `prefetch_related` (ManyToMany) batches queries. Both eliminate N+1 query problems.

---

## Error Handling Conventions

### WARNING: Bare except Clauses

**The Problem:**

```python
# BAD - Catches everything including KeyboardInterrupt
try:
    user.save()
except:
    logger.error('Save failed')
```

**Why This Breaks:**
1. Catches `KeyboardInterrupt` (Ctrl+C) and `SystemExit` - prevents graceful shutdown
2. Hides bugs by catching `NameError`, `AttributeError`, etc.
3. Makes debugging impossible - no stack trace, no error details

**The Fix:**

```python
# GOOD - Catch specific exceptions
from django.db import IntegrityError

try:
    user.save()
except IntegrityError as e:
    logger.error(f'Duplicate email: {e}')
    raise ValidationError('Email already exists')
except Exception as e:
    logger.exception('Unexpected error during save')
    raise
```

**When You Might Be Tempted:** When you're unsure what exceptions might occur. Instead: let it crash in dev, then catch specific exceptions.

### Exception Chaining

```python
# GOOD - Preserve original exception context
try:
    response = requests.post(url, json=data, timeout=5)
    response.raise_for_status()
except requests.RequestException as e:
    raise TurnstileVerificationError('CAPTCHA verification failed') from e
```

**Why:** `from e` preserves the original stack trace for debugging.

### Early Returns (Guard Clauses)

```python
# GOOD - Flat structure, easy to follow
def register_user(email, password):
    if not email:
        raise ValueError('Email required')
    
    if len(password) < 8:
        raise ValueError('Password too short')
    
    if CustomUser.objects.filter(email=email).exists():
        raise ValueError('Email already registered')
    
    # Main logic at single indentation level
    user = CustomUser.objects.create_user(email, password)
    return user

# AVOID - Nested indentation (cognitive overload)
def register_user(email, password):
    if email:
        if len(password) >= 8:
            if not CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.create_user(email, password)
                return user
            else:
                raise ValueError('Email already registered')
        else:
            raise ValueError('Password too short')
    else:
        raise ValueError('Email required')
```

**Why:** Guard clauses reduce nesting, improve readability, and make the "happy path" obvious.

---

## Async Patterns

### Async Views with Django 5.x

```python
# users/views.py
from django.http import JsonResponse
import httpx

async def check_email_availability(request):
    """Async view for email validation API"""
    email = request.GET.get('email')
    
    # Async HTTP call (non-blocking)
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://api.example.com/validate?email={email}')
        data = response.json()
    
    return JsonResponse({'available': data['valid']})
```

**When to use:** I/O-bound operations (HTTP requests, external APIs). Django 5.x supports async views natively.

### WARNING: Sync Code in Async Context

**The Problem:**

```python
# BAD - Blocks the event loop
async def user_dashboard(request):
    users = CustomUser.objects.all()  # Sync ORM call in async function
    return render(request, 'dashboard.html', {'users': users})
```

**Why This Breaks:**
1. Django ORM is synchronous - blocks the entire async event loop
2. Negates all benefits of async (no concurrency)
3. Can cause deadlocks in production ASGI servers

**The Fix:**

```python
# GOOD - Use sync_to_async for ORM calls
from asgiref.sync import sync_to_async

async def user_dashboard(request):
    users = await sync_to_async(list)(CustomUser.objects.all())
    return render(request, 'dashboard.html', {'users': users})
```

**When You Might Be Tempted:** When mixing async views with Django ORM. Always wrap ORM calls with `sync_to_async`.

---

## Memory and Performance

### Generator Expressions for Large Datasets

```python
# GOOD - Memory-efficient (lazy evaluation)
user_emails = (u.email for u in CustomUser.objects.iterator())
for email in user_emails:
    send_email(email)  # Processes one at a time

# BAD - Loads all into memory
user_emails = [u.email for u in CustomUser.objects.all()]
```

**Why:** Generators yield items one at a time, avoiding memory spikes with large datasets.

### QuerySet iterator() for Bulk Processing

```python
# GOOD - Streams results (low memory)
for user in CustomUser.objects.iterator(chunk_size=1000):
    process_user(user)

# BAD - Loads entire table into memory
for user in CustomUser.objects.all():
    process_user(user)
```

**Why:** `.iterator()` bypasses Django's query cache, processing rows in batches.