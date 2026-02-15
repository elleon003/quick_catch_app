# Services Reference

## Contents
- Service Layer Architecture
- Business Logic Patterns
- Email Services
- Authentication Services
- Anti-Patterns

---

## Service Layer Architecture

Django views should delegate business logic to **service functions** or **service classes**. This project uses **function-based services** for simplicity.

### Service Layer Pattern

```
View Layer (views.py)          →  Handles HTTP, validation, rendering
    ↓
Service Layer (services.py)    →  Business logic, transactions
    ↓
Data Layer (models.py)         →  Database access, ORM queries
```

**Key Principle:** Views handle HTTP concerns (request/response). Services handle business logic (workflows, calculations, external APIs).

---

## Business Logic in Services

### DO: Extract Business Logic to Services

```python
# users/services.py
from django.db import transaction
from .models import CustomUser, AuthProvider

def create_user_with_provider(email, password, provider_type='email'):
    """
    Create user and associated auth provider in a transaction.
    Returns (user, auth_provider) tuple.
    """
    with transaction.atomic():
        user = CustomUser.objects.create_user(email=email, password=password)
        auth_provider = AuthProvider.objects.create(
            user=user,
            provider=provider_type,
            provider_user_id=email
        )
        return user, auth_provider

# users/views.py
from .services import create_user_with_provider

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user, _ = create_user_with_provider(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            login(request, user)
            return redirect('users:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
```

### DON'T: Put Business Logic in Views

```python
# BAD - Business logic mixed with HTTP handling
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # BAD - Complex business logic in view
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            auth_provider = AuthProvider.objects.create(
                user=user,
                provider='email',
                provider_user_id=form.cleaned_data['email']
            )
            # More logic...
            login(request, user)
            return redirect('users:dashboard')
```

**Why This Breaks:**
1. **Untestable** - Can't test business logic without HTTP mocks
2. **Not reusable** - Can't call from management commands, Celery tasks, or APIs
3. **Violates SRP** - View does HTTP AND business logic
4. **Transaction management** - Hard to ensure atomicity

---

## Email Services

### Magic Link Email Service

```python
# users/services.py
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from sesame.utils import get_token

def send_magic_link_email(request, user):
    """
    Generate and email a magic link for passwordless login.
    """
    token = get_token(user)
    magic_url = request.build_absolute_uri(reverse('users:magic_login', args=[token]))
    
    subject = 'Your Login Link'
    message = f'Click here to log in: {magic_url}\n\nThis link expires in 1 hour.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
```

**Usage in View:**

```python
# users/views.py
from .services import send_magic_link_email

def request_magic_link_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            send_magic_link_email(request, user)
            return render(request, 'users/magic_link_sent.html')
        except CustomUser.DoesNotExist:
            # Security: Don't reveal if email exists
            return render(request, 'users/magic_link_sent.html')
```

**Why Service Function:** Email logic is reusable from views, management commands, or APIs. Testable in isolation.

---

## Authentication Services

### Multi-Provider Linking Service

```python
# users/services.py
from .models import AuthProvider, AuthLinkingToken
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

def create_auth_linking_token(user, provider):
    """
    Create a temporary token for linking a new auth provider to existing user.
    """
    token = get_random_string(32)
    expires_at = timezone.now() + timedelta(minutes=10)
    
    AuthLinkingToken.objects.create(
        user=user,
        provider=provider,
        token=token,
        expires_at=expires_at
    )
    return token

def link_auth_provider(token, provider_user_id):
    """
    Link a new auth provider using a temporary token.
    Returns user if successful, None if token invalid.
    """
    try:
        linking_token = AuthLinkingToken.objects.get(
            token=token,
            expires_at__gt=timezone.now()
        )
        
        # Create AuthProvider
        AuthProvider.objects.create(
            user=linking_token.user,
            provider=linking_token.provider,
            provider_user_id=provider_user_id
        )
        
        # Delete used token
        linking_token.delete()
        
        return linking_token.user
    except AuthLinkingToken.DoesNotExist:
        return None
```

---

## Turnstile CAPTCHA Service

```python
# users/turnstile.py
import requests
from django.conf import settings

def verify_turnstile(token, remote_ip=None):
    """
    Verify Cloudflare Turnstile CAPTCHA token.
    Returns True if valid, False otherwise.
    """
    if not settings.TURNSTILE_SECRET_KEY:
        # Graceful degradation if not configured
        return True
    
    url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    data = {
        'secret': settings.TURNSTILE_SECRET_KEY,
        'response': token,
    }
    if remote_ip:
        data['remoteip'] = remote_ip
    
    try:
        response = requests.post(url, data=data, timeout=5)
        result = response.json()
        return result.get('success', False)
    except (requests.RequestException, ValueError):
        # Fail open on network errors (security tradeoff)
        return False
```

**Usage in Forms:**

```python
# users/forms.py
from .turnstile import verify_turnstile

class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()
        
        # Verify Turnstile
        turnstile_token = self.data.get('cf-turnstile-response')
        if not verify_turnstile(turnstile_token):
            raise forms.ValidationError('CAPTCHA verification failed.')
        
        return cleaned_data
```

---

## WARNING: Service Layer Anti-Patterns

### Anti-Pattern 1: God Services

**The Problem:**

```python
# BAD - One service does everything
class UserService:
    def create_user(self, email, password): ...
    def update_profile(self, user, data): ...
    def send_email(self, user, subject, message): ...
    def verify_captcha(self, token): ...
    def link_social_account(self, user, provider): ...
    def export_user_data(self, user): ...
    def generate_magic_link(self, user): ...
    # ... 20 more methods
```

**Why This Breaks:**
1. **Impossible to test** - One class has too many responsibilities
2. **High coupling** - Changes affect unrelated functionality
3. **Hard to navigate** - Finding relevant code requires scanning hundreds of lines
4. **Import hell** - Service imports everything it might need

**The Fix:**

```python
# GOOD - Focused service modules
# users/services/user_creation.py
def create_user_with_provider(email, password, provider_type): ...

# users/services/email.py
def send_magic_link_email(request, user): ...
def send_verification_email(user): ...

# users/services/auth_linking.py
def create_auth_linking_token(user, provider): ...
def link_auth_provider(token, provider_user_id): ...
```

**When You Might Be Tempted:** Starting with a single `services.py` is fine. When it exceeds 200 lines, split into `services/` directory with focused modules.

---

### Anti-Pattern 2: Services That Return HTTP Responses

**The Problem:**

```python
# BAD - Service returns HTTP response
def create_user_service(request):
    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        user = CustomUser.objects.create_user(...)
        login(request, user)
        return redirect('users:dashboard')  # BAD - HTTP concern
    else:
        return render(request, 'register.html', {'form': form})  # BAD
```

**Why This Breaks:**
1. **Not reusable** - Can't call from management commands or APIs
2. **Tight coupling** - Service depends on Django views/templates
3. **Hard to test** - Must mock HTTP request/response

**The Fix:**

```python
# GOOD - Service returns domain objects, view handles HTTP
def create_user_with_provider(email, password, provider_type='email'):
    with transaction.atomic():
        user = CustomUser.objects.create_user(email=email, password=password)
        auth_provider = AuthProvider.objects.create(...)
        return user, auth_provider

# View handles HTTP
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user, _ = create_user_with_provider(...)
            login(request, user)
            return redirect('users:dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
```

---

### Anti-Pattern 3: No Transaction Management

**The Problem:**

```python
# BAD - No atomicity guarantees
def create_user_with_provider(email, password, provider_type):
    user = CustomUser.objects.create_user(email=email, password=password)
    # If this fails, user is created but orphaned (no AuthProvider)
    auth_provider = AuthProvider.objects.create(
        user=user,
        provider=provider_type,
        provider_user_id=email
    )
    return user, auth_provider
```

**Why This Breaks:**
1. **Partial failures** - User created but AuthProvider creation fails → orphaned user
2. **Data inconsistency** - User exists without tracking which auth method they used
3. **Hard to debug** - Inconsistent state is difficult to reproduce

**The Fix:**

```python
# GOOD - Atomic transaction
from django.db import transaction

def create_user_with_provider(email, password, provider_type='email'):
    with transaction.atomic():
        user = CustomUser.objects.create_user(email=email, password=password)
        auth_provider = AuthProvider.objects.create(
            user=user,
            provider=provider_type,
            provider_user_id=email
        )
        return user, auth_provider
```

**When You Might Be Tempted:** Single-operation services don't need transactions. Multi-operation workflows ALWAYS need `transaction.atomic()`.