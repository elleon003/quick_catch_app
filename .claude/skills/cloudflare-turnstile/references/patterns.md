# Turnstile Integration Patterns

## Contents
- Server-Side Verification Pattern
- Frontend Widget Integration
- Graceful Degradation Pattern
- Anti-Patterns and Security Issues

---

## Server-Side Verification Pattern

The project implements server-side verification in `users/turnstile.py`. NEVER trust client-side validation alone.

### The Correct Pattern

```python
# users/turnstile.py
import requests
from django.conf import settings

def verify_turnstile(token: str, request) -> bool:
    """
    Verify Turnstile token with Cloudflare API.
    
    Returns True if verification succeeds or keys not configured.
    Returns False if verification fails.
    """
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    
    # Graceful degradation - if keys not configured, allow through
    if not site_key or not secret_key:
        return True
    
    # Empty token means user didn't complete challenge
    if not token:
        return False
    
    # Verify with Cloudflare API
    response = requests.post(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        json={
            'secret': secret_key,
            'response': token,
            'remoteip': request.META.get('REMOTE_ADDR', '')
        },
        timeout=5
    )
    
    data = response.json()
    return data.get('success', False)
```

**Why This Works:**
1. **Timeout protection** - 5s timeout prevents hanging requests
2. **IP validation** - Cloudflare validates the IP matches the challenge
3. **Graceful degradation** - Works without keys configured (dev environments)
4. **Explicit failure** - Empty token returns False, not True

### View Integration Pattern

```python
# users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from .turnstile import verify_turnstile

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # CRITICAL: Verify Turnstile BEFORE processing form data
            token = form.cleaned_data.get('turnstile_token', '')
            if not verify_turnstile(token, request):
                form.add_error(None, 'CAPTCHA verification failed. Please try again.')
                return render(request, 'registration/register.html', {'form': form})
            
            # Only proceed if verification passed
            user = form.save()
            messages.success(request, 'Registration successful!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
```

**Order Matters:**
1. Form validation first (Django built-in checks)
2. Turnstile verification second (bot protection)
3. Business logic last (user creation, database writes)

---

## Frontend Widget Integration

### Custom Widget Pattern

```python
# users/turnstile.py
from django.forms.widgets import HiddenInput
from django.conf import settings
from django.utils.safestring import mark_safe

def get_turnstile_widget():
    """
    Returns a widget that renders Cloudflare Turnstile challenge.
    
    Widget is hidden input that Turnstile JS populates with token.
    """
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    
    class TurnstileWidget(HiddenInput):
        def render(self, name, value, attrs=None, renderer=None):
            hidden_input = super().render(name, value, attrs, renderer)
            
            # If no site key configured, return just the hidden input (graceful degradation)
            if not site_key:
                return hidden_input
            
            # Render Turnstile widget div
            turnstile_div = f'''
                <div class="cf-turnstile my-4" 
                     data-sitekey="{site_key}"
                     data-callback="onTurnstileSuccess"
                     data-theme="light"></div>
                <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
                <script>
                function onTurnstileSuccess(token) {{
                    document.querySelector('input[name="{name}"]').value = token;
                }}
                </script>
            '''
            
            return mark_safe(hidden_input + turnstile_div)
    
    return TurnstileWidget()
```

**Why This Approach:**
1. **Extends HiddenInput** - Plays nicely with Django form rendering
2. **Callback function** - Populates hidden field when challenge completes
3. **Theme attribute** - Can be customized to match site design
4. **Async script loading** - Doesn't block page rendering
5. **Graceful degradation** - Returns basic input if keys missing

### Template Integration

```html
<!-- theme/templates/registration/register.html -->
{% extends 'base.html' %}
{% load static %}

{% block content %}
<form method="post" class="max-w-md mx-auto">
    {% csrf_token %}
    
    <!-- Standard Django form fields -->
    <div class="form-control">
        <label class="label">{{ form.email.label_tag }}</label>
        {{ form.email }}
    </div>
    
    <!-- Turnstile widget renders automatically -->
    {{ form.turnstile_token }}
    
    <button type="submit" class="btn btn-primary">Register</button>
</form>
{% endblock %}
```

---

## Graceful Degradation Pattern

This project implements graceful degradation: forms work even without Turnstile keys configured.

### Why Graceful Degradation

**Development Scenarios:**
- New developers cloning repo without setting up Turnstile
- CI/CD pipelines without Cloudflare credentials
- Local testing without internet connection
- Staging environments that don't need bot protection

### Implementation

```python
# users/forms.py
from django import forms
from .turnstile import get_turnstile_widget

class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    # CRITICAL: required=False for graceful degradation
    turnstile_token = forms.CharField(
        widget=get_turnstile_widget(),
        required=False,  # Allows form to submit without token
        label=''
    )
```

**Verification Logic:**

```python
def verify_turnstile(token: str, request) -> bool:
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    
    # If keys not configured, allow through (development mode)
    if not site_key or not secret_key:
        return True  # Graceful degradation
    
    # If keys ARE configured but token empty, fail (bot or user error)
    if not token:
        return False
    
    # Verify with API
    # ...
```

---

## WARNING: Common Anti-Patterns

### Anti-Pattern 1: Client-Side Only Validation

**The Problem:**

```python
# BAD - Only checking if token exists, not verifying it
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # This is useless - bots can inject fake tokens
            if form.cleaned_data.get('turnstile_token'):
                user = form.save()
```

**Why This Breaks:**
1. **Bots bypass trivially** - Can inject any string as token
2. **No cryptographic verification** - Token isn't validated with Cloudflare
3. **False sense of security** - Appears protected but isn't

**The Fix:**

```python
# GOOD - Server-side verification with Cloudflare API
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get('turnstile_token', '')
            if not verify_turnstile(token, request):  # Actual API call
                form.add_error(None, 'Verification failed')
                return render(request, 'template.html', {'form': form})
            user = form.save()
```

### Anti-Pattern 2: Reusing Tokens

**The Problem:**

```python
# BAD - Storing token for reuse
class User(models.Model):
    last_turnstile_token = models.CharField(max_length=500)

def verify_user(user, token):
    if token == user.last_turnstile_token:
        return True  # Token already verified before
```

**Why This Breaks:**
1. **Tokens are one-time use** - Cloudflare rejects reused tokens
2. **Replay attacks** - Attacker captures token, reuses indefinitely
3. **No time-bound validation** - Old tokens shouldn't work forever

**The Fix:**

```python
# GOOD - Verify fresh token every time
def form_view(request):
    token = request.POST.get('cf-turnstile-response', '')
    if not verify_turnstile(token, request):  # Fresh verification each time
        return HttpResponse('Invalid CAPTCHA', status=400)
```

### Anti-Pattern 3: Missing Timeout

**The Problem:**

```python
# BAD - No timeout, can hang indefinitely
def verify_turnstile(token, request):
    response = requests.post(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        json={'secret': SECRET_KEY, 'response': token}
        # Missing timeout parameter
    )
    return response.json().get('success', False)
```

**Why This Breaks:**
1. **User experience degradation** - Page hangs for 60+ seconds
2. **Resource exhaustion** - Blocked threads/workers waiting for response
3. **Cascading failures** - If Cloudflare API slow, entire site slows

**The Fix:**

```python
# GOOD - 5 second timeout with exception handling
def verify_turnstile(token, request):
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            json={'secret': SECRET_KEY, 'response': token},
            timeout=5  # Fail fast
        )
        return response.json().get('success', False)
    except requests.Timeout:
        # Log error, but don't expose to user
        return False
```

### Anti-Pattern 4: Exposing Secret Key to Frontend

**The Problem:**

```html
<!-- BAD - Secret key in JavaScript -->
<script>
const TURNSTILE_SECRET = '1x0000000000000000000000000000000AA';
fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: JSON.stringify({secret: TURNSTILE_SECRET, response: token})
});
</script>
```

**Why This Breaks:**
1. **Complete security bypass** - Bots use your secret to verify their own tokens
2. **Visible in page source** - Anyone can inspect and steal
3. **Violates trust model** - Secrets NEVER belong in client code

**The Fix:**

```html
<!-- GOOD - Only site key (public) in frontend -->
<div class="cf-turnstile" data-sitekey="{{ TURNSTILE_SITE_KEY }}"></div>

<!-- Verification happens server-side in Django view -->