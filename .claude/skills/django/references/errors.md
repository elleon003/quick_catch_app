# Errors Reference

## Contents
- Error Handling Patterns
- Form Validation
- Custom Error Pages
- Logging
- Anti-Patterns

---

## Error Handling Patterns

### Try-Except with Specific Exceptions

```python
# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from .models import CustomUser

def user_profile_view(request, user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return render(request, 'errors/404.html', status=404)
    except ValidationError as e:
        return render(request, 'errors/400.html', {'error': str(e)}, status=400)
    
    return render(request, 'users/profile.html', {'profile_user': user})
```

**Pattern:** Catch specific exceptions. NEVER use bare `except:` (catches KeyboardInterrupt, SystemExit).

### Using get_object_or_404

```python
# GOOD - Django shortcut for common pattern
from django.shortcuts import get_object_or_404

def user_profile_view(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    return render(request, 'users/profile.html', {'profile_user': user})
```

**Why:** Raises `Http404` automatically if object not found. Cleaner than try-except.

---

## Form Validation

### Form-Level Validation

```python
# users/forms.py
from django import forms
from .models import CustomUser
from .turnstile import verify_turnstile

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')
    
    def clean_password2(self):
        """Field-level validation: passwords match."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2
    
    def clean_email(self):
        """Field-level validation: email unique."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email
    
    def clean(self):
        """Form-level validation: CAPTCHA."""
        cleaned_data = super().clean()
        
        turnstile_token = self.data.get('cf-turnstile-response')
        if not verify_turnstile(turnstile_token):
            raise forms.ValidationError('CAPTCHA verification failed.')
        
        return cleaned_data
```

**Validation Levels:**
1. **Field-level:** `clean_<fieldname>()` - validates single field
2. **Form-level:** `clean()` - validates across multiple fields

### Displaying Form Errors

```django
<!-- theme/templates/registration/register.html -->
<form method="post">
    {% csrf_token %}
    
    <!-- Non-field errors (from clean()) -->
    {% if form.non_field_errors %}
        <div class="alert alert-error">
            {{ form.non_field_errors }}
        </div>
    {% endif %}
    
    <!-- Field-specific errors -->
    <div class="form-control">
        {{ form.email.label_tag }}
        {{ form.email }}
        {% if form.email.errors %}
            <span class="error">{{ form.email.errors }}</span>
        {% endif %}
    </div>
    
    <button type="submit">Register</button>
</form>
```

---

## Custom Error Pages

### 404 and 500 Error Templates

```python
# config/settings/base.py
DEBUG = False  # Required for custom error pages to work

# config/urls.py
handler404 = 'theme.views.custom_404_view'
handler500 = 'theme.views.custom_500_view'
```

### Custom Error Views

```python
# theme/views.py
from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)
```

### Error Templates

```django
<!-- theme/templates/errors/404.html -->
{% extends 'base.html' %}

{% block content %}
<div class="text-center">
    <h1 class="text-6xl font-bold">404</h1>
    <p class="text-xl">Page not found</p>
    <a href="{% url 'home' %}" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}
```

**Pattern:** Custom error pages only work when `DEBUG=False`. Test in production settings.

---

## Logging

### Logging Configuration

```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'users': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
```

### Using Loggers in Code

```python
# users/views.py
import logging

logger = logging.getLogger('users')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.email}")
            return redirect('users:dashboard')
        else:
            logger.warning(f"Registration failed: {form.errors}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
```

**Log Levels:**
- `DEBUG` - Detailed debugging info
- `INFO` - General informational messages
- `WARNING` - Warning messages (potential issues)
- `ERROR` - Error messages (handled exceptions)
- `CRITICAL` - Critical errors (system failure)

---

## WARNING: Error Handling Anti-Patterns

### Anti-Pattern 1: Bare Except Clauses

**The Problem:**

```python
# BAD - Catches everything including system exits
try:
    user = CustomUser.objects.get(email=email)
except:  # NEVER do this
    user = None
```

**Why This Breaks:**
1. **Catches KeyboardInterrupt** - Can't stop the process with Ctrl+C
2. **Catches SystemExit** - Prevents clean shutdown
3. **Hides bugs** - Silently catches programming errors (NameError, AttributeError)
4. **Hard to debug** - No indication what went wrong

**The Fix:**

```python
# GOOD - Catch specific exceptions
try:
    user = CustomUser.objects.get(email=email)
except CustomUser.DoesNotExist:
    user = None
except CustomUser.MultipleObjectsReturned:
    logger.error(f"Multiple users with email {email}")
    user = None
```

**When You Might Be Tempted:** NEVER use bare `except:`. Always specify exception types. Use `except Exception:` as last resort (still bad, but less bad).

---

### Anti-Pattern 2: Silent Failures

**The Problem:**

```python
# BAD - Error occurs but user sees nothing
def send_magic_link_email(request, user):
    try:
        token = get_token(user)
        magic_url = request.build_absolute_uri(reverse('users:magic_login', args=[token]))
        send_mail('Login Link', f'Click here: {magic_url}', 'noreply@example.com', [user.email])
    except Exception:
        pass  # BAD - Silent failure, user never knows email didn't send
```

**Why This Breaks:**
1. **No user feedback** - User waits for email that never arrives
2. **No debugging info** - Can't diagnose email server issues
3. **Poor UX** - User assumes system is working when it's not

**The Fix:**

```python
# GOOD - Log error and inform user
import logging
logger = logging.getLogger('users')

def send_magic_link_email(request, user):
    try:
        token = get_token(user)
        magic_url = request.build_absolute_uri(reverse('users:magic_login', args=[token]))
        send_mail('Login Link', f'Click here: {magic_url}', 'noreply@example.com', [user.email])
        return True
    except Exception as e:
        logger.error(f"Failed to send magic link to {user.email}: {str(e)}")
        return False

# In view
if send_magic_link_email(request, user):
    messages.success(request, 'Login link sent to your email.')
else:
    messages.error(request, 'Failed to send login link. Please try again later.')
```

---

### Anti-Pattern 3: Returning Internal Errors to Users

**The Problem:**

```python
# BAD - Exposes internal implementation details
def login_view(request):
    if request.method == 'POST':
        try:
            email = request.POST['email']
            password = request.POST['password']
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return redirect('dashboard')
        except Exception as e:
            # BAD - Shows technical error to user
            return render(request, 'login.html', {'error': str(e)})
```

**Why This Breaks:**
1. **Security risk** - Exposes database structure, stack traces, file paths
2. **Information leakage** - Attackers learn about system internals
3. **Poor UX** - Technical jargon confuses users

**The Fix:**

```python
# GOOD - Map internal errors to user-friendly messages
import logging
logger = logging.getLogger('users')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('users:dashboard')
        else:
            # Form validation provides user-friendly errors
            return render(request, 'registration/login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})
```

**Security Principle:** Log detailed errors server-side. Show generic messages to users ("Login failed" instead of "User with email user@example.com does not exist").

---

## Validation Best Practices

### Input Validation at Boundaries

```python
# GOOD - Validate all user input
from django import forms
from django.core.validators import EmailValidator

class ContactForm(forms.Form):
    email = forms.EmailField(validators=[EmailValidator()])
    message = forms.CharField(max_length=1000)
    
    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters.")
        return message
```

**Principle:** Validate at **system boundaries** (user input, external APIs). Trust internal code.

### Defensive Programming for External Data

```python
# users/services.py
import requests

def verify_turnstile(token, remote_ip=None):
    """Verify Turnstile CAPTCHA token with defensive error handling."""
    if not token:
        return False
    
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={'secret': settings.TURNSTILE_SECRET_KEY, 'response': token},
            timeout=5  # CRITICAL: Always set timeout
        )
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        result = response.json()
        return result.get('success', False)
    except requests.RequestException as e:
        logger.error(f"Turnstile verification failed: {str(e)}")
        return False  # Fail open (allow access) or fail closed (deny access)
    except ValueError:  # JSON decode error
        logger.error("Turnstile returned invalid JSON")
        return False
```

**Pattern:** External API calls ALWAYS need timeouts, exception handling, and defensive parsing.