---
name: cloudflare-turnstile
description: |
  Integrates Cloudflare Turnstile CAPTCHA protection in forms
  Use when: Adding bot protection to registration, login, or any user-facing forms; replacing reCAPTCHA with privacy-friendly alternative
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Cloudflare Turnstile Skill

Cloudflare Turnstile provides CAPTCHA protection without privacy concerns or accessibility barriers. This project uses a custom integration in `users/turnstile.py` that verifies tokens server-side and provides frontend helpers for Django forms. Unlike reCAPTCHA, Turnstile runs primarily invisible challenges and respects user privacy.

## Quick Start

### Add Turnstile to Django Form

```python
# users/forms.py
from django import forms
from .turnstile import get_turnstile_widget

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    turnstile_token = forms.CharField(
        widget=get_turnstile_widget(),
        required=False  # Graceful degradation if keys not configured
    )
```

### Verify Token in View

```python
# users/views.py
from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .turnstile import verify_turnstile

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Verify Turnstile token
            token = form.cleaned_data.get('turnstile_token', '')
            if not verify_turnstile(token, request):
                form.add_error(None, 'CAPTCHA verification failed. Please try again.')
                return render(request, 'registration/register.html', {'form': form})
            
            # Proceed with registration
            # ...
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| **Site Key** | Public key for frontend widget | `TURNSTILE_SITE_KEY` in settings |
| **Secret Key** | Private key for server verification | `TURNSTILE_SECRET_KEY` in settings |
| **Token** | One-time challenge response from client | `cf-turnstile-response` form field |
| **Graceful Degradation** | Form works without keys configured | `required=False` on token field |
| **Test Keys** | Development keys for testing | Site: `1x00000000000000000000AA` |

## Common Patterns

### Form with Turnstile Widget

**When:** Any form that needs bot protection (registration, login, contact forms)

```python
from django import forms
from .turnstile import get_turnstile_widget

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    turnstile_token = forms.CharField(
        widget=get_turnstile_widget(),
        required=False
    )
```

### Server-Side Verification

**When:** Processing any form with Turnstile protection

```python
from .turnstile import verify_turnstile

def form_view(request):
    if request.method == 'POST':
        form = MyForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get('turnstile_token', '')
            if not verify_turnstile(token, request):
                form.add_error(None, 'Verification failed')
                return render(request, 'template.html', {'form': form})
            # Process form
```

### Environment Configuration

**When:** Setting up Turnstile for development or production

```bash
# .env.dev or .env
TURNSTILE_SITE_KEY=your-site-key-here
TURNSTILE_SECRET_KEY=your-secret-key-here

# Development test keys (always pass)
TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
```

### Template Rendering

**When:** Displaying form with Turnstile widget

```html
<!-- theme/templates/registration/register.html -->
{% load static %}
<form method="post">
    {% csrf_token %}
    {{ form.email }}
    {{ form.password }}
    {{ form.turnstile_token }}  {# Renders widget automatically #}
    <button type="submit">Register</button>
</form>
```

## Configuration

### Get Turnstile Keys

1. Visit [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to Turnstile section
3. Create new site with your domain (`localhost` for dev)
4. Choose "Managed" challenge type
5. Copy Site Key and Secret Key to environment variables

### Settings Integration

```python
# config/settings/base.py
import os

TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', '')
```

## See Also

- [patterns](references/patterns.md) - Integration patterns and anti-patterns
- [workflows](references/workflows.md) - Setup and testing workflows

## Related Skills

- **django** - Form handling and view patterns
- **python** - Environment variable management
- **frontend-design** - Widget styling with Tailwind/DaisyUI