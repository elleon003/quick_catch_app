# Python Errors Reference

## Contents
- Common Django Errors
- Import and Module Errors
- Database and ORM Errors
- HTTP and View Errors
- Authentication Errors
- Type Errors

---

## Common Django Errors

### ImproperlyConfigured

```python
# Error: django.core.exceptions.ImproperlyConfigured: Requested setting DEBUG, but settings are not configured

# Cause: Django settings not loaded
# Fix: Set DJANGO_SETTINGS_MODULE environment variable
export DJANGO_SETTINGS_MODULE=config.settings.development

# Or in Python:
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
```

### AppRegistryNotReady

```python
# Error: django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet

# Cause: Accessing models before Django is initialized
# Bad:
from users.models import CustomUser
user = CustomUser.objects.first()  # Fails if Django not ready

# Fix: Ensure django.setup() is called (or use django.setup() in scripts)
import django
django.setup()
from users.models import CustomUser
```

**When:** Writing management commands or standalone scripts. Django automatically calls `setup()` for views/tests.

### SECRET_KEY Missing

```python
# Error: KeyError: 'SECRET_KEY'

# Cause: SECRET_KEY not set in environment
# Fix: Add to .env file or set environment variable
SECRET_KEY=django-insecure-generate-a-real-key-here

# Or in settings:
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
```

**Production:** NEVER commit real `SECRET_KEY` to git. Use environment variables.

---

## Import and Module Errors

### ModuleNotFoundError

```python
# Error: ModuleNotFoundError: No module named 'users'

# Cause 1: App not in INSTALLED_APPS
# Fix: Add to config/settings/base.py
INSTALLED_APPS = [
    # ...
    'users',
]

# Cause 2: App directory missing __init__.py
# Fix: Create empty file
touch users/__init__.py

# Cause 3: Virtual environment not activated
# Fix: Activate venv
source .venv/bin/activate
pip install -r requirements.txt
```

### ImportError: cannot import name

```python
# Error: ImportError: cannot import name 'CustomUser' from partially initialized module 'users.models'

# Cause: Circular import (models.py imports views.py, views.py imports models.py)
# Fix: Use late import or TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .views import register_view
```

**Debug:** Add `print(f"Importing {__name__}")` at top of files to trace import order.

### WARNING: Relative Import Beyond Top-Level Package

**The Problem:**

```python
# users/views.py
from ..config.settings import base  # BAD - Goes above package

# Error: ValueError: attempted relative import beyond top-level package
```

**Why This Breaks:**
1. Relative imports only work within a package
2. Going above the package root (`..`) is undefined behavior

**The Fix:**

```python
# GOOD - Use absolute import
from config.settings import base

# Or import settings properly:
from django.conf import settings
print(settings.DEBUG)
```

---

## Database and ORM Errors

### DoesNotExist

```python
# Error: users.models.CustomUser.DoesNotExist: CustomUser matching query does not exist

# Cause: get() called with no matching record
user = CustomUser.objects.get(email='notfound@example.com')  # Raises DoesNotExist

# Fix 1: Use filter() which returns empty QuerySet
users = CustomUser.objects.filter(email='notfound@example.com')
if users.exists():
    user = users.first()

# Fix 2: Use get_or_create()
user, created = CustomUser.objects.get_or_create(
    email='user@example.com',
    defaults={'first_name': 'John'}
)

# Fix 3: Catch exception
from django.core.exceptions import ObjectDoesNotExist

try:
    user = CustomUser.objects.get(email='notfound@example.com')
except CustomUser.DoesNotExist:
    user = None
```

**Rule:** Use `.get()` when you EXPECT exactly one result. Use `.filter()` for uncertain queries.

### MultipleObjectsReturned

```python
# Error: users.models.CustomUser.MultipleObjectsReturned: get() returned more than one CustomUser

# Cause: get() called on non-unique field
user = CustomUser.objects.get(first_name='John')  # Multiple Johns exist

# Fix: Use filter() and iterate, or add more specific filters
users = CustomUser.objects.filter(first_name='John', last_name='Doe')
if users.count() == 1:
    user = users.first()
```

### IntegrityError

```python
# Error: django.db.utils.IntegrityError: UNIQUE constraint failed: users_customuser.email

# Cause: Attempting to save duplicate value for unique field
from django.db import IntegrityError

try:
    CustomUser.objects.create_user(email='duplicate@example.com', password='pass')
    CustomUser.objects.create_user(email='duplicate@example.com', password='pass')  # Fails
except IntegrityError as e:
    print(f'Duplicate email: {e}')

# Fix: Check existence before creating
if not CustomUser.objects.filter(email='duplicate@example.com').exists():
    CustomUser.objects.create_user(email='duplicate@example.com', password='pass')
```

### OperationalError: no such table

```python
# Error: django.db.utils.OperationalError: no such table: users_customuser

# Cause: Migrations not applied
# Fix: Run migrations
python manage.py migrate

# Check migration status:
python manage.py showmigrations

# If models changed, create new migration:
python manage.py makemigrations
python manage.py migrate
```

**Debug Workflow:**
1. `makemigrations` - Generate migration files from model changes
2. `showmigrations` - Check which migrations are applied
3. `migrate` - Apply pending migrations

---

## HTTP and View Errors

### NoReverseMatch

```python
# Error: django.urls.exceptions.NoReverseMatch: Reverse for 'user_settings' not found

# Cause: URL name not defined or typo
return redirect('user_settings')  # 'user_settings' doesn't exist

# Fix: Check urls.py for correct name
# users/urls.py
urlpatterns = [
    path('settings/', views.user_settings_view, name='user_settings'),  # Matches!
]

# Or use URL pattern directly:
return redirect('/users/settings/')
```

### TemplateDoesNotExist

```python
# Error: django.template.exceptions.TemplateDoesNotExist: user_settings.html

# Cause: Template not in TEMPLATES dirs or wrong path
return render(request, 'user_settings.html')  # Can't find template

# Fix 1: Check TEMPLATES setting
TEMPLATES = [{
    'DIRS': [BASE_DIR / 'theme' / 'templates'],  # Must contain template
}]

# Fix 2: Verify file exists
theme/templates/user_settings.html  # Should exist

# Debug: Print template search paths
from django.template.loader import get_template
try:
    get_template('user_settings.html')
except Exception as e:
    print(e)  # Shows search paths
```

### CSRF Verification Failed

```python
# Error: Forbidden (403): CSRF verification failed

# Cause 1: Missing {% csrf_token %} in form
# Fix:
<form method="post">
    {% csrf_token %}  # Required for POST
    <button type="submit">Submit</button>
</form>

# Cause 2: AJAX request without CSRF token
# Fix: Include token in AJAX header
fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
})

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
```

---

## Authentication Errors

### AttributeError: 'AnonymousUser' object has no attribute 'email'

```python
# Error: AttributeError: 'AnonymousUser' object has no attribute 'email'

# Cause: Accessing user attributes without checking authentication
@login_required
def dashboard_view(request):
    print(request.user.email)  # Works - @login_required guarantees authenticated user

def public_view(request):
    print(request.user.email)  # FAILS if not logged in

# Fix: Check is_authenticated first
def public_view(request):
    if request.user.is_authenticated:
        print(request.user.email)
    else:
        print('Anonymous user')
```

### SuspiciousOperation: Invalid HTTP_HOST header

```python
# Error: django.core.exceptions.SuspiciousOperation: Invalid HTTP_HOST header: 'malicious.com'

# Cause: Request has Host header not in ALLOWED_HOSTS
# Fix: Add domain to settings
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'yourdomain.com',
    'www.yourdomain.com',
]

# Development: Allow all hosts (INSECURE)
ALLOWED_HOSTS = ['*']  # Only for local dev!
```

---

## Type Errors

### TypeError: 'NoneType' object is not subscriptable

```python
# Error: TypeError: 'NoneType' object is not subscriptable

# Cause: Accessing None as if it's a dict/list
user = CustomUser.objects.filter(email='notfound@example.com').first()  # Returns None
print(user['email'])  # FAILS - user is None

# Fix: Check for None
user = CustomUser.objects.filter(email='notfound@example.com').first()
if user is not None:
    print(user.email)  # Safe
```

### TypeError: 'QuerySet' object is not callable

```python
# Error: TypeError: 'QuerySet' object is not callable

# Cause: Calling QuerySet as function (typo: parentheses instead of square brackets)
users = CustomUser.objects.all()
first_user = users(0)  # BAD - () instead of []

# Fix: Use list indexing or .first()
first_user = users[0]  # Index
first_user = users.first()  # Method (safer - returns None if empty)
```

### WARNING: Truthy Checks on QuerySets

**The Problem:**

```python
# BAD - QuerySet is always truthy even if empty
users = CustomUser.objects.filter(is_active=False)
if users:  # WRONG - This is True even for empty QuerySet
    print('Has inactive users')
```

**Why This Breaks:**
1. Empty QuerySets evaluate to `True` in boolean context
2. Triggers database query just for the check
3. Logic error: treats "no results" as "has results"

**The Fix:**

```python
# GOOD - Use .exists() (doesn't fetch rows)
users = CustomUser.objects.filter(is_active=False)
if users.exists():  # Correct - checks if any rows match
    print('Has inactive users')

# Or count if you need the number:
count = users.count()
if count > 0:
    print(f'Has {count} inactive users')
```

**When You Might Be Tempted:** When porting code from lists to QuerySets. Always use `.exists()` for boolean checks.