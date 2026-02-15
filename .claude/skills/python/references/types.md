# Python Types Reference

## Contents
- Type Hints and Annotations
- Django Model Field Types
- Collection Types
- Optional and Union Types
- Generic Types
- Type Checking Tools

---

## Type Hints and Annotations

### Function Signatures

```python
from typing import Optional, List, Dict

def get_user_by_email(email: str) -> Optional['CustomUser']:
    """Type hints document expected inputs and outputs"""
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None

def get_active_users(limit: int = 10) -> List['CustomUser']:
    """Return list of active users"""
    return list(CustomUser.objects.filter(is_active=True)[:limit])

def user_to_dict(user: 'CustomUser') -> Dict[str, str]:
    """Convert user to dictionary"""
    return {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
```

**Why:** Type hints improve IDE autocomplete, catch bugs early, and serve as inline documentation.

### WARNING: Using str When You Need Union Types

**The Problem:**

```python
# BAD - Stringly-typed code
def set_auth_provider(provider_type: str) -> None:
    """provider_type should be 'google', 'linkedin', or 'email'"""
    # But nothing prevents: set_auth_provider('twitter')  # Typo goes undetected!
    pass
```

**Why This Breaks:**
1. No IDE autocomplete for valid values
2. Typos pass type checking
3. Forces runtime validation and error messages

**The Fix:**

```python
# GOOD - Use Literal or Enum
from typing import Literal
from enum import Enum

# Option 1: Literal (for simple cases)
ProviderType = Literal['google', 'linkedin', 'email', 'magic_link']

def set_auth_provider(provider_type: ProviderType) -> None:
    pass  # IDE warns if invalid value passed

# Option 2: Enum (for complex cases)
class AuthProviderType(Enum):
    GOOGLE = 'google'
    LINKEDIN = 'linkedin'
    EMAIL = 'email'
    MAGIC_LINK = 'magic_link'

def set_auth_provider(provider_type: AuthProviderType) -> None:
    pass

# Usage:
set_auth_provider(AuthProviderType.GOOGLE)  # Type-safe
```

**When You Might Be Tempted:** When there are only 2-3 string options. Use Literal anyway - it's worth it.

---

## Django Model Field Types

### Common Field Types

```python
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class CustomUser(AbstractBaseUser):
    """User model with explicit field types"""
    
    # Text fields
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Boolean fields (default=False unless specified)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # DateTime fields (auto_now_add for creation, auto_now for updates)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    USERNAME_FIELD = 'email'  # Type: str (field name, not field instance)
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []  # Type: List[str]
```

### Relationship Field Types

```python
from django.db import models
from django.conf import settings

class AuthProvider(models.Model):
    """Tracks authentication methods per user"""
    
    # ForeignKey (many-to-one)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Reference via settings for custom user
        on_delete=models.CASCADE,  # Delete providers when user deleted
        related_name='auth_providers'
    )
    
    # CharField with choices (enforces enum-like behavior)
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google OAuth2'),
        ('linkedin', 'LinkedIn OAuth2'),
        ('magic_link', 'Magic Link'),
    ]
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    
    # JSONField (store arbitrary data)
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = [['user', 'provider_type']]  # Composite unique constraint
```

**Why:** Django model fields define database schema AND Python types. Use `choices` for enum-like behavior.

### WARNING: null=True vs blank=True Confusion

**The Problem:**

```python
# BAD - Inconsistent handling of "no value"
class User(models.Model):
    bio = models.TextField(null=True)  # Allows NULL in DB but not blank forms
    website = models.URLField(blank=True)  # Allows blank forms but stores empty string ''
```

**Why This Breaks:**
1. `null=True` creates two "empty" states: `None` (NULL) and `''` (empty string)
2. Queries must check both: `bio__isnull=True` AND `bio=''`
3. Forms reject blank input unless `blank=True` is set

**The Fix:**

```python
# GOOD - Use blank=True for string fields (store '' not NULL)
class User(models.Model):
    bio = models.TextField(blank=True, default='')
    
# GOOD - Use null=True for non-string fields (dates, foreign keys)
class User(models.Model):
    last_login = models.DateTimeField(null=True, blank=True)
    profile_image = models.ForeignKey('Image', null=True, blank=True, on_delete=models.SET_NULL)
```

**Rule:** For string fields (`CharField`, `TextField`, `EmailField`), use `blank=True` only. For other fields, use both `null=True` and `blank=True`.

---

## Collection Types

### List, Dict, Set, Tuple

```python
from typing import List, Dict, Set, Tuple

def process_users(
    user_ids: List[int],  # Ordered, duplicates allowed
    settings: Dict[str, str],  # Key-value pairs
    unique_emails: Set[str],  # Unordered, no duplicates
    coordinates: Tuple[float, float],  # Fixed size, immutable
) -> None:
    pass

# Usage:
process_users(
    user_ids=[1, 2, 3],
    settings={'theme': 'dark', 'lang': 'en'},
    unique_emails={'a@ex.com', 'b@ex.com'},
    coordinates=(40.7128, -74.0060)
)
```

### Django QuerySets Are Not Lists

```python
from django.db.models import QuerySet

# QuerySet type (lazy, not evaluated until iterated)
users_qs: QuerySet['CustomUser'] = CustomUser.objects.filter(is_active=True)

# Convert to list (evaluates query)
users_list: List['CustomUser'] = list(users_qs)

# Type hint for function accepting either
from typing import Union, Iterable
def process_users(users: Union[QuerySet['CustomUser'], List['CustomUser']]) -> None:
    # Or more general:
    # users: Iterable['CustomUser']
    for user in users:
        print(user.email)
```

**Why:** QuerySets are lazy and chainable. Lists are eager and in-memory. Know the difference.

---

## Optional and Union Types

### Optional for Nullable Values

```python
from typing import Optional

def get_user_by_id(user_id: int) -> Optional['CustomUser']:
    """Returns user or None if not found"""
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return None

# Usage requires None check:
user = get_user_by_id(1)
if user is not None:
    print(user.email)  # Safe - type checker knows user is not None
```

**Note:** `Optional[X]` is shorthand for `Union[X, None]`.

### Union for Multiple Return Types

```python
from typing import Union
from django.http import HttpResponse, JsonResponse

def api_or_html(request) -> Union[JsonResponse, HttpResponse]:
    """Return JSON for API, HTML for browser"""
    if request.accepts('application/json'):
        return JsonResponse({'status': 'ok'})
    return HttpResponse('<h1>OK</h1>')
```

---

## Generic Types

### TypeVar for Generic Functions

```python
from typing import TypeVar, List

T = TypeVar('T')

def first(items: List[T]) -> T:
    """Return first item - type matches input"""
    return items[0]

# Type checker knows:
user = first([CustomUser(), CustomUser()])  # Returns CustomUser
num = first([1, 2, 3])  # Returns int
```

### Django Generic Views with Types

```python
from django.views.generic import ListView
from typing import Any

class UserListView(ListView):
    model = CustomUser
    template_name = 'users/list.html'
    context_object_name = 'users'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['total_users'] = CustomUser.objects.count()
        return context
```

---

## Type Checking Tools

### mypy for Static Type Checking

```bash
# Install mypy
pip install mypy

# Run type checker
mypy users/

# Configure in pyproject.toml or mypy.ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

# Ignore third-party packages without type stubs
[mypy-social_django.*]
ignore_missing_imports = True
```

### Django Stubs for Better Type Checking

```bash
# Install Django type stubs
pip install django-stubs

# Add to mypy config
[mypy]
plugins = mypy_django_plugin.main

[mypy_django_plugin]
django_settings_module = config.settings.development
```

**Why:** mypy catches type errors before runtime. Django stubs provide types for Django's internals.

### WARNING: Any Type Everywhere

**The Problem:**

```python
# BAD - Defeats the purpose of type hints
from typing import Any

def process_data(data: Any) -> Any:
    return data.get('email')  # Type checker can't help - data could be anything
```

**Why This Breaks:**
1. No autocomplete in IDE
2. Type checker can't catch errors
3. Equivalent to no type hints at all

**The Fix:**

```python
# GOOD - Use specific types
from typing import Dict

def process_data(data: Dict[str, str]) -> str:
    return data.get('email', '')  # Type checker warns if key missing
```

**When You Might Be Tempted:** When interfacing with untyped third-party code. Instead, define TypedDict or Protocol for the expected shape.