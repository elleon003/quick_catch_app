# Python Modules Reference

## Contents
- Django App Structure
- Package Organization
- Import Patterns
- Circular Import Prevention
- Module Discovery and INSTALLED_APPS

---

## Django App Structure

### Standard Django App Layout

```
users/                      # Django app (single responsibility)
├── __init__.py            # Makes directory a Python package
├── models.py              # Database models (CustomUser, etc.)
├── auth_models.py         # Related models (AuthProvider, AuthLinkingToken)
├── views.py               # View functions (register_view, login_view)
├── forms.py               # Django forms (CustomUserCreationForm)
├── urls.py                # URL patterns for this app
├── admin.py               # Django admin configuration
├── apps.py                # App configuration
├── turnstile.py           # Utility module (CAPTCHA verification)
├── tests.py               # Unit tests (or tests/ directory)
└── migrations/            # Database migration files
    ├── __init__.py
    └── 0001_initial.py
```

**Why:** Django apps are self-contained modules with clear responsibilities. One app = one feature domain.

### Project Configuration Layout

```
config/                    # Project-wide configuration
├── __init__.py
├── settings/              # Split settings pattern
│   ├── __init__.py       # Settings loader (checks DJANGO_ENV)
│   ├── base.py           # Shared settings
│   ├── development.py    # Dev-specific settings
│   └── production.py     # Prod-specific settings
├── urls.py               # Root URL configuration
├── wsgi.py               # WSGI entry point
└── asgi.py               # ASGI entry point (async)
```

**Pattern:** Split settings keep environment-specific config separate. `config/settings/__init__.py` loads the right module based on `DJANGO_ENV`.

---

## Package Organization

### Splitting Large Modules

```python
# users/models.py - Getting too large
# BEFORE (all in one file):
class CustomUserManager(BaseUserManager): ...  # 50 lines
class CustomUser(AbstractBaseUser): ...        # 100 lines
class AuthProvider(models.Model): ...          # 30 lines
class AuthLinkingToken(models.Model): ...      # 40 lines

# AFTER (split by concern):
# users/models.py - Core user model
from django.contrib.auth.models import AbstractBaseUser
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    objects = CustomUserManager()

# users/managers.py - Custom manager logic
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields): ...

# users/auth_models.py - Authentication-related models
from django.db import models

class AuthProvider(models.Model): ...
class AuthLinkingToken(models.Model): ...
```

**Rule:** Split modules when they exceed ~200 lines or when distinct concepts emerge.

### __init__.py for Clean Imports

```python
# users/__init__.py - Expose public API
from .models import CustomUser
from .auth_models import AuthProvider, AuthLinkingToken

__all__ = ['CustomUser', 'AuthProvider', 'AuthLinkingToken']

# Now external code can import cleanly:
from users import CustomUser  # Instead of: from users.models import CustomUser
```

**Why:** `__init__.py` defines the public interface of your package.

---

## Import Patterns

### PEP 8 Import Order (Standard)

```python
# users/views.py - Standard import order
# 1. Standard library
import os
from datetime import datetime, timedelta

# 2. Django core
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

# 3. Third-party packages
from social_django.models import UserSocialAuth
import requests

# 4. Local application
from .models import CustomUser
from .forms import CustomUserCreationForm
from .turnstile import verify_turnstile
```

**Enforce:** Use `isort` to automatically sort imports: `pip install isort && isort users/`

### Absolute vs Relative Imports

```python
# users/views.py - Both work, pick one style

# ABSOLUTE - Clear but verbose
from users.models import CustomUser
from users.forms import CustomUserCreationForm

# RELATIVE - Concise within same app (preferred for Django apps)
from .models import CustomUser
from .forms import CustomUserCreationForm

# MIXED - Use absolute for cross-app imports
from users.models import CustomUser  # From another app
from .forms import CustomUserCreationForm  # Within same app
```

**Recommendation:** Use relative imports (`.`) within the same Django app, absolute for cross-app imports.

### WARNING: Star Imports

**The Problem:**

```python
# BAD - Imports everything, pollutes namespace
from django.contrib.auth.models import *

user = User()  # Which User? From auth or local app?
```

**Why This Breaks:**
1. No way to know where names come from
2. Name collisions silently override earlier imports
3. IDE can't autocomplete or navigate

**The Fix:**

```python
# GOOD - Explicit imports
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Or import module if you need many items:
from django.contrib.auth import models as auth_models

user = auth_models.User()
```

**When You Might Be Tempted:** When you need 5+ names from one module. Import the module instead: `import module`.

---

## Circular Import Prevention

### WARNING: Circular Imports

**The Problem:**

```python
# users/models.py
from .views import register_view  # Imports views

class CustomUser(models.Model):
    def get_registration_url(self):
        return register_view  # Uses view in model

# users/views.py
from .models import CustomUser  # Imports models

def register_view(request):
    CustomUser.objects.create_user(...)  # Uses model in view
```

**Why This Breaks:**
1. Python imports modules top-to-bottom
2. `models.py` tries to import `views.py` before finishing its own import
3. Results in `ImportError: cannot import name 'CustomUser'`

**The Fix - Option 1: Move to separate module**

```python
# users/urls.py - Keep URL logic here (not in models)
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
]

# users/models.py - Use URL names, not view functions
from django.urls import reverse

class CustomUser(models.Model):
    def get_registration_url(self):
        return reverse('register')  # No import needed
```

**The Fix - Option 2: Late import**

```python
# users/models.py
class CustomUser(models.Model):
    def send_welcome_email(self):
        from .email import send_email  # Import inside method
        send_email(self.email, 'Welcome!')
```

**When You Might Be Tempted:** When models need to reference views or vice versa. Use `reverse()` for URLs, late imports for utilities.

### Type Hints and Circular Imports

```python
# users/models.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import only for type checking (not runtime)
    from .auth_models import AuthProvider

class CustomUser(models.Model):
    def get_providers(self) -> list['AuthProvider']:  # Forward reference as string
        return list(self.auth_providers.all())
```

**Why:** `TYPE_CHECKING` is `False` at runtime, preventing circular imports. String annotations defer evaluation.

---

## Module Discovery and INSTALLED_APPS

### Registering Django Apps

```python
# config/settings/base.py
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'tailwind',
    'theme',  # django-tailwind theme app
    'django_browser_reload',
    'social_django',
    
    # Local apps (this project)
    'users',  # Must be listed for Django to discover models/migrations
]
```

**Critical:** Django only discovers models, migrations, admin, and management commands from apps listed in `INSTALLED_APPS`.

### App Configuration

```python
# users/apps.py - Configure app metadata
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'
    
    def ready(self):
        """Run code when Django starts"""
        # Import signals to register handlers
        from . import signals  # noqa: F401
```

**Why:** `AppConfig.ready()` runs once when Django starts. Use for signal registration, startup checks, etc.

### Package-Level __init__.py

```python
# users/__init__.py - Set default app config
default_app_config = 'users.apps.UsersConfig'
```

**Note:** Django 3.2+ auto-discovers `AppConfig`, so this is optional. Include for backward compatibility.

---

## Virtual Environment and Package Management

### Creating and Activating venv

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install project dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

**Why:** Virtual environments isolate project dependencies from system Python.

### requirements.txt Management

```bash
# Install package and add to requirements.txt
pip install django-ninja
pip freeze | grep django-ninja >> requirements.txt

# Or manually edit requirements.txt and run:
pip install -r requirements.txt

# Check for outdated packages
pip-review  # Installed in this project

# Interactively update packages
pip-review --interactive
```

**Pattern:** This project uses `pip-review` for dependency updates. See `requirements.txt`.