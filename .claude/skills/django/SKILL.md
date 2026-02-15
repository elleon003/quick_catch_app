---
name: django
description: |
  Manages Django models, views, URLs, middleware, and application architecture
  Use when: Creating models, views, URLs, middleware, authentication flows, or managing Django apps
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Django Skill

This project uses Django 5.2 with a split settings architecture (development/production), custom email-based authentication, and a multi-auth strategy supporting traditional login, social OAuth2 (Google, LinkedIn), and magic links. Django Ninja is installed for API development.

## Quick Start

### Custom User Model (Email-Based)

```python
# users/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
```

### Function-Based Views with Login Required

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard_view(request):
    auth_providers = AuthProvider.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {
        'user': request.user,
        'auth_providers': auth_providers,
    })
```

### URL Configuration Pattern

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('social_django.urls', namespace='social')),
]
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| Split Settings | Use `DJANGO_ENV` to load environment-specific config | `config/settings/{base,development,production}.py` |
| Custom User Model | Email authentication instead of username | `AUTH_USER_MODEL = 'users.CustomUser'` |
| Function-Based Views | Preferred pattern in this codebase | `@login_required` decorator |
| Template Inheritance | All templates extend `base.html` | `{% extends 'base.html' %}` |
| Multi-Auth Tracking | `AuthProvider` model tracks connected methods | `email`, `google`, `linkedin`, `magic_link` |

## Common Patterns

### Creating a New Django App

**When:** Adding a new feature domain (blog, shop, api)

```bash
# Create app
python manage.py startapp myapp

# Add to config/settings/base.py INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'myapp',
]

# Create templates in theme/templates/myapp/
# Create URL patterns in myapp/urls.py
# Include URLs in config/urls.py
```

### Migrations Workflow

**When:** After model changes

```bash
# Generate migrations
python manage.py makemigrations

# Review generated migration files
# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Protected View Pattern

**When:** Creating authenticated-only views

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def protected_view(request):
    if not request.user.is_verified:
        return redirect('verify_email')
    
    context = {'data': get_user_data(request.user)}
    return render(request, 'protected.html', context)
```

## See Also

- [routes](references/routes.md) - URL patterns and routing configuration
- [services](references/services.md) - Business logic and service layer patterns
- [database](references/database.md) - ORM queries, migrations, transactions
- [auth](references/auth.md) - Multi-auth, social login, magic links
- [errors](references/errors.md) - Error handling and validation patterns

## Related Skills

- **python** - Python language patterns and best practices
- **postgresql** - Production database configuration
- **redis** - Caching and session storage
- **django-social-auth** - Google and LinkedIn OAuth2 integration
- **django-sesame** - Magic link authentication
- **cloudflare-turnstile** - CAPTCHA protection for forms
- **django-ninja** - FastAPI-style API framework (installed, not yet configured)
- **tailwind** - Frontend styling framework
- **daisyui** - UI component library