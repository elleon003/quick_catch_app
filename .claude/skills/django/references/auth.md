# Authentication Reference

## Contents
- Custom User Model Architecture
- Multi-Auth Strategy
- Social Authentication (Google, LinkedIn)
- Magic Links (Passwordless Auth)
- CAPTCHA Protection
- Auth Decorators and Mixins
- Anti-Patterns

---

## Custom User Model Architecture

This project uses **email-based authentication** instead of Django's default username-based system.

### Custom User Model

```python
# users/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # CRITICAL: Hashes password
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
```

**Settings Configuration:**

```python
# config/settings/base.py
AUTH_USER_MODEL = 'users.CustomUser'
```

**Why Email-Based:** Modern UX expectation, eliminates "forgot username" issues, simplifies social auth integration.

---

## Multi-Auth Strategy

Users can authenticate via **multiple methods** (email/password, Google, LinkedIn, magic links). The `AuthProvider` model tracks connected methods.

### AuthProvider Model

```python
# users/auth_models.py
from django.db import models
from django.conf import settings

class AuthProvider(models.Model):
    PROVIDER_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
        ('linkedin', 'LinkedIn'),
        ('magic_link', 'Magic Link'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['provider', 'provider_user_id']]
```

**Query Patterns:**

```python
# Check which auth methods user has
auth_providers = AuthProvider.objects.filter(user=request.user)
has_password = auth_providers.filter(provider='email').exists()
has_google = auth_providers.filter(provider='google').exists()

# Find user by social auth
try:
    provider = AuthProvider.objects.get(provider='google', provider_user_id='google-id-123')
    user = provider.user
except AuthProvider.DoesNotExist:
    user = None
```

---

## Social Authentication (Django Social Auth)

### Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    'social_django',
]

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# LinkedIn OAuth2
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = os.environ.get('LINKEDIN_CLIENT_ID')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']

# Redirect URLs
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/'
```

### Social Auth URLs

```python
# config/urls.py
urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
]
```

### Template Integration

```django
<!-- theme/templates/registration/login.html -->
<div class="social-auth">
    <a href="{% url 'social:begin' 'google-oauth2' %}" class="btn btn-outline">
        Sign in with Google
    </a>
    <a href="{% url 'social:begin' 'linkedin-oauth2' %}" class="btn btn-outline">
        Sign in with LinkedIn
    </a>
</div>
```

**OAuth Flow:**
1. User clicks "Sign in with Google" → redirects to Google
2. User authorizes → Google redirects to `/complete/google-oauth2/`
3. Django Social Auth validates, creates/updates user, logs them in
4. Redirects to `LOGIN_REDIRECT_URL`

See the **django-social-auth** skill for advanced patterns (account linking, custom pipelines).

---

## Magic Links (Django Sesame)

Passwordless authentication via **one-time email links**.

### Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    'sesame',
]

AUTHENTICATION_BACKENDS = (
    'sesame.backends.ModelBackend',  # Magic link backend
    'django.contrib.auth.backends.ModelBackend',
)

# Magic link settings
SESAME_MAX_AGE = 3600  # 1 hour expiration
SESAME_ONE_TIME = True  # Single-use tokens
```

### Generating Magic Links

```python
# users/services.py
from sesame.utils import get_token
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

def send_magic_link_email(request, user):
    """Generate and email a magic link for passwordless login."""
    token = get_token(user)
    magic_url = request.build_absolute_uri(reverse('users:magic_login', args=[token]))
    
    subject = 'Your Login Link'
    message = f'Click here to log in: {magic_url}\n\nThis link expires in 1 hour.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
```

### Magic Link View

```python
# users/views.py
from django.contrib.auth import login
from sesame.utils import get_user

def magic_login_view(request, token):
    """Handle magic link authentication."""
    user = get_user(token)
    if user is None:
        return render(request, 'users/magic_link_invalid.html')
    
    login(request, user, backend='sesame.backends.ModelBackend')
    
    # Track magic link usage
    AuthProvider.objects.get_or_create(
        user=user,
        provider='magic_link',
        defaults={'provider_user_id': user.email}
    )
    
    return redirect('users:dashboard')
```

See the **django-sesame** skill for advanced usage.

---

## CAPTCHA Protection (Cloudflare Turnstile)

Protects registration and login forms from bots.

### Turnstile Verification

```python
# users/turnstile.py
import requests
from django.conf import settings

def verify_turnstile(token, remote_ip=None):
    """Verify Cloudflare Turnstile CAPTCHA token."""
    if not settings.TURNSTILE_SECRET_KEY:
        return True  # Graceful degradation
    
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
        return False  # Fail open on errors
```

### Form Integration

```python
# users/forms.py
from django.contrib.auth.forms import AuthenticationForm
from .turnstile import verify_turnstile

class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()
        
        # Verify Turnstile CAPTCHA
        turnstile_token = self.data.get('cf-turnstile-response')
        if not verify_turnstile(turnstile_token):
            raise forms.ValidationError('CAPTCHA verification failed. Please try again.')
        
        return cleaned_data
```

See the **cloudflare-turnstile** skill for template integration.

---

## Auth Decorators and Mixins

### Function-Based View Protection

```python
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'user': request.user})
```

### Class-Based View Protection

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/users/login/'  # Optional: override LOGIN_URL
```

### Permission-Based Protection

```python
from django.contrib.auth.decorators import user_passes_test

def is_verified(user):
    return user.is_authenticated and user.is_verified

@user_passes_test(is_verified, login_url='/verify/')
def verified_only_view(request):
    return render(request, 'verified.html')
```

---

## WARNING: Authentication Anti-Patterns

### Anti-Pattern 1: Storing Passwords in Plain Text

**The Problem:**

```python
# BAD - NEVER store plain text passwords
user = CustomUser(email='user@example.com')
user.password = 'plaintext123'  # CRITICAL SECURITY VULNERABILITY
user.save()
```

**Why This Breaks:**
1. **Database breach = credential theft** - Attackers get every password
2. **Violates security standards** - OWASP, PCI-DSS mandate hashing
3. **Legal liability** - Data breach lawsuits, regulatory fines

**The Fix:**

```python
# GOOD - Always use .set_password() or .create_user()
user = CustomUser.objects.create_user(email='user@example.com', password='plaintext123')
# Or
user = CustomUser(email='user@example.com')
user.set_password('plaintext123')  # Hashes with PBKDF2 by default
user.save()
```

**When You Might Be Tempted:** NEVER. No exceptions. Always hash passwords using Django's built-in methods.

---

### Anti-Pattern 2: Using `authenticate()` Without `login()`

**The Problem:**

```python
# BAD - User authenticated but not logged in
from django.contrib.auth import authenticate

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # BAD - User authenticated but session not created
            return redirect('dashboard')
```

**Why This Breaks:**
1. **Session not created** - `request.user` is still `AnonymousUser`
2. **Broken auth flow** - User redirected to dashboard but sees login prompt
3. **Confusing debugging** - Looks like auth works but fails silently

**The Fix:**

```python
# GOOD - Authenticate AND login
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # CRITICAL: Creates session
            return redirect('users:dashboard')
```

---

### Anti-Pattern 3: Inconsistent AuthProvider Tracking

**The Problem:**

```python
# BAD - Social auth creates user but no AuthProvider tracking
# User logged in via Google, but system doesn't track it
user = authenticate(...)
login(request, user)
# Missing: AuthProvider.objects.create(user=user, provider='google', ...)
```

**Why This Breaks:**
1. **Lost audit trail** - Can't determine which auth methods user has used
2. **Account linking fails** - Can't prevent duplicate accounts from same social ID
3. **Settings page broken** - Can't display "Connected Accounts"

**The Fix:**

```python
# GOOD - Track every authentication method
# After social auth
AuthProvider.objects.get_or_create(
    user=user,
    provider='google',
    defaults={'provider_user_id': social_user_id}
)

# After magic link
AuthProvider.objects.get_or_create(
    user=user,
    provider='magic_link',
    defaults={'provider_user_id': user.email}
)
```

**When You Might Be Tempted:** Always track auth providers when users authenticate. Use Django Social Auth pipelines or post-login signals.