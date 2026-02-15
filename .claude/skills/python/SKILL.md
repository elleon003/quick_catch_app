---
name: python
description: |
  Handles Python code patterns, virtual environments, and package management.
  Use when: Writing Python code, managing dependencies, debugging Python errors, working with Django apps
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Python Skill

This project uses Python 3.12+ with Django 5.2. Python code follows PEP 8 conventions with `snake_case` naming, type hints where beneficial, and a focus on readability. Virtual environments (`.venv`) isolate dependencies. Package management uses `pip` with `requirements.txt` and `pip-review` for updates.

## Quick Start

### Creating a New Django App Module

```python
# users/models.py - Custom user model pattern
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
```

### Environment-Based Configuration

```python
# config/settings/__init__.py - Settings loader pattern
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.dev')  # or .env for production

# Determine which settings module to use
env = os.environ.get('DJANGO_ENV', 'development')
if env == 'production':
    from .production import *
else:
    from .development import *
```

### Import Order (PEP 8)

```python
# Standard library
import os
from datetime import datetime

# Django core
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Third-party
from social_django.models import UserSocialAuth
import requests

# Local application
from .forms import CustomUserCreationForm
from .models import CustomUser
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| Virtual Environment | Isolates project dependencies | `.venv/` directory |
| Package Management | `requirements.txt` for dependencies | `pip install -r requirements.txt` |
| Type Hints | Optional but recommended for clarity | `def get_user(user_id: int) -> CustomUser:` |
| Naming Conventions | `snake_case` for functions/variables | `user_settings`, `register_view` |
| Class Naming | `PascalCase` for classes | `CustomUser`, `AuthProvider` |
| Constants | `SCREAMING_SNAKE_CASE` | `LOGIN_REDIRECT_URL` |
| Boolean Prefixes | `is_`, `has_`, `should_` | `is_authenticated`, `has_permission` |

## Common Patterns

### View Functions with Decorators

**When:** Creating protected views in Django

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard_view(request):
    """User dashboard - requires authentication"""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)
```

### Environment Variable Access

**When:** Reading configuration from `.env` files

```python
import os

# Required variables (fail fast if missing)
SECRET_KEY = os.environ['SECRET_KEY']

# Optional with defaults
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Database configuration with fallback to SQLite
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
    }
}
```

### Model Managers for Custom Queries

**When:** Adding reusable query logic to models

```python
from django.db import models

class CustomUserManager(models.Manager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a user with email and password"""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
```

### Error Handling with Specific Exceptions

**When:** Catching and handling predictable errors

```python
from django.core.exceptions import ValidationError
from django.db import IntegrityError

try:
    user.save()
except IntegrityError:
    # Handle duplicate email
    return render(request, 'register.html', {
        'error': 'Email already exists'
    })
except ValidationError as e:
    # Handle validation errors
    return render(request, 'register.html', {
        'error': str(e)
    })
```

## See Also

- [patterns](references/patterns.md) - Idiomatic Python patterns and Django conventions
- [types](references/types.md) - Type hints and data structures
- [modules](references/modules.md) - Package organization and imports
- [errors](references/errors.md) - Common Python and Django errors

## Related Skills

- **django** - Full Django framework patterns and conventions
- **postgresql** - Database queries and ORM usage
- **redis** - Caching and session storage in Python
- **docker** - Running Python apps in containers