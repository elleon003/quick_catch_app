# Routes Reference

## Contents
- URL Configuration Architecture
- URL Pattern Naming
- Namespacing and Includes
- Common Routing Patterns
- Anti-Patterns

---

## URL Configuration Architecture

This project uses a **split URL configuration** with root URLs in `config/urls.py` and app-specific URLs in each app's `urls.py`.

### Root URL Configuration

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from theme import views as theme_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('', theme_views.home_view, name='home'),
]
```

**Key Pattern:** App-specific routes are prefixed (`users/`, `api/`) and delegated to app URL modules.

### App-Specific URL Configuration

```python
# users/urls.py
from django.urls import path
from . import views

app_name = 'users'  # Namespace for reverse lookups

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('settings/', views.user_settings_view, name='settings'),
    path('magic/<str:token>/', views.magic_login_view, name='magic_login'),
]
```

**URL Naming Convention:** Use descriptive verbs (`register`, `login`, `dashboard`) without redundant prefixes since the namespace already provides context.

---

## URL Pattern Naming

### DO: Use Named URL Patterns

```python
# GOOD - Named patterns enable reverse lookups
path('dashboard/', views.dashboard_view, name='dashboard'),

# In views
from django.urls import reverse
redirect_url = reverse('users:dashboard')

# In templates
{% url 'users:dashboard' %}
```

### DON'T: Hardcode URLs

```python
# BAD - Brittle, breaks when URLs change
redirect('/users/dashboard/')

# BAD - In templates
<a href="/users/dashboard/">Dashboard</a>
```

**Why This Breaks:** When you change the URL structure (`/users/dashboard/` → `/account/dashboard/`), every hardcoded reference breaks. Named patterns are refactored automatically via `reverse()` and `{% url %}`.

---

## Path Converters and Dynamic Routes

### Built-in Path Converters

```python
# users/urls.py
urlpatterns = [
    path('magic/<str:token>/', views.magic_login_view, name='magic_login'),
    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('posts/<slug:slug>/', views.post_detail_view, name='post_detail'),
]
```

**Available Converters:**
- `str` - Non-empty string excluding `/`
- `int` - Positive integers
- `slug` - ASCII letters, numbers, hyphens, underscores
- `uuid` - UUID format
- `path` - Any string including `/`

### Custom Path Converters

```python
# users/converters.py
class EmailConverter:
    regex = r'[^@]+@[^@]+\.[^@]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value

# users/urls.py
from django.urls import path, register_converter
from .converters import EmailConverter

register_converter(EmailConverter, 'email')

urlpatterns = [
    path('verify/<email:user_email>/', views.verify_email_view, name='verify_email'),
]
```

---

## Namespacing and Includes

### App Namespacing Pattern

```python
# users/urls.py
app_name = 'users'  # CRITICAL: Define namespace

urlpatterns = [
    path('login/', views.login_view, name='login'),
]

# config/urls.py
urlpatterns = [
    path('users/', include('users.urls')),  # Namespace: 'users'
]

# Reverse lookup
reverse('users:login')  # → '/users/login/'
```

### Third-Party App Namespacing

```python
# config/urls.py
urlpatterns = [
    # Social auth URLs with explicit namespace
    path('', include('social_django.urls', namespace='social')),
]

# In templates
{% url 'social:begin' 'google-oauth2' %}  # → '/login/google-oauth2/'
```

**Why Namespacing Matters:** Without namespaces, `reverse('login')` is ambiguous if multiple apps define a `login` URL. Namespaces provide unambiguous resolution.

---

## Common Routing Patterns

### RESTful Resource Routes

```python
# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/', views.post_list_view, name='post_list'),           # GET list
    path('posts/create/', views.post_create_view, name='post_create'), # GET form, POST create
    path('posts/<int:pk>/', views.post_detail_view, name='post_detail'),  # GET detail
    path('posts/<int:pk>/edit/', views.post_edit_view, name='post_edit'), # GET form, POST update
    path('posts/<int:pk>/delete/', views.post_delete_view, name='post_delete'), # POST delete
]
```

**Naming Convention:** `<resource>_<action>` (e.g., `post_list`, `post_create`).

---

## WARNING: Common Routing Anti-Patterns

### Anti-Pattern 1: Redundant Namespace Prefixes

**The Problem:**

```python
# BAD - Redundant 'user' prefix in names
app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='user_login'),  # Redundant
    path('dashboard/', views.dashboard_view, name='user_dashboard'),  # Redundant
]

# Results in: reverse('users:user_login') - awkward
```

**Why This Breaks:**
1. Namespace already provides context (`users:login` is clear)
2. Creates awkward reverse lookups (`users:user_login`)
3. Violates DRY principle

**The Fix:**

```python
# GOOD - Namespace provides context
app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]

# Clean reverse: reverse('users:login')
```

---

### Anti-Pattern 2: Using `re_path` for Simple Patterns

**The Problem:**

```python
# BAD - Regex overkill for simple patterns
from django.urls import re_path

urlpatterns = [
    re_path(r'^posts/(?P<pk>\d+)/$', views.post_detail_view, name='post_detail'),
]
```

**Why This Breaks:**
1. Harder to read and maintain
2. `path()` with converters is clearer and performs better
3. Regex is error-prone (e.g., missing `^` or `$`)

**The Fix:**

```python
# GOOD - Use path() with converters
from django.urls import path

urlpatterns = [
    path('posts/<int:pk>/', views.post_detail_view, name='post_detail'),
]
```

**When You Might Be Tempted:** Legacy Django code used `url()` (now `re_path()`). Only use `re_path()` for truly complex patterns that converters can't handle.

---

### Anti-Pattern 3: Missing Trailing Slashes

**The Problem:**

```python
# BAD - Inconsistent trailing slashes
urlpatterns = [
    path('login', views.login_view, name='login'),      # No trailing slash
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Has trailing slash
]
```

**Why This Breaks:**
1. Django's `APPEND_SLASH` setting redirects `/login` → `/login/`, causing extra request
2. Inconsistent URL structure confuses users and developers
3. SEO issues with duplicate content

**The Fix:**

```python
# GOOD - Consistent trailing slashes (Django convention)
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
```

---

## Integration with Settings

### Environment-Specific URL Configuration

```python
# config/urls.py
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
]

# Development-only: Django Browser Reload
if settings.DEBUG:
    urlpatterns += [
        path('__reload__/', include('django_browser_reload.urls')),
    ]
```

**Pattern:** Use `if settings.DEBUG` to conditionally include development tools (debug toolbar, browser reload, etc.).

---

## Django Ninja API Routes

Django Ninja is installed but not configured yet. When adding API routes:

```python
# api/urls.py
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/users")
def list_users(request):
    return [{"id": 1, "email": "user@example.com"}]

# config/urls.py
from api.urls import api

urlpatterns = [
    path('api/', api.urls),  # All API routes under /api/
]
```

See the **django-ninja** skill for detailed API routing patterns.