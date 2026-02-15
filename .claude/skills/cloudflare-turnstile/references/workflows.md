# Turnstile Workflows

## Contents
- Initial Setup Workflow
- Adding Turnstile to New Forms
- Testing and Debugging
- Production Deployment

---

## Initial Setup Workflow

### 1. Get Cloudflare Turnstile Keys

Copy this checklist and track progress:

- [ ] Visit [Cloudflare Dashboard](https://dash.cloudflare.com/)
- [ ] Navigate to "Turnstile" section in sidebar
- [ ] Click "Add Site"
- [ ] Fill in site configuration:
  - Domain: `localhost` (development) or your production domain
  - Widget mode: "Managed" (recommended - invisible when possible)
  - Challenge type: "Managed" (lets Cloudflare decide)
- [ ] Copy Site Key (public key for frontend)
- [ ] Copy Secret Key (private key for backend verification)
- [ ] Store keys in password manager (DO NOT commit to git)

### 2. Configure Environment Variables

**For local development:**

```bash
# Edit .env.dev (already exists in project)
TURNSTILE_SITE_KEY=1x00000000000000000000AA  # Test key for development
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA  # Test key

# Or use your real keys from Cloudflare
TURNSTILE_SITE_KEY=0x4AAAAAAAY0123456789
TURNSTILE_SECRET_KEY=0x4AAAAAAAY_secretkey_123456789
```

**For Docker development:**

```bash
# Edit .env.docker
cp .env.docker.example .env.docker
# Add keys to .env.docker (git-ignored)
TURNSTILE_SITE_KEY=your-site-key
TURNSTILE_SECRET_KEY=your-secret-key
```

**For production:**

```bash
# Set environment variables in hosting platform
export TURNSTILE_SITE_KEY=0x4AAAAAAAY0123456789
export TURNSTILE_SECRET_KEY=0x4AAAAAAAY_secretkey_123456789
```

### 3. Verify Settings Configuration

```python
# config/settings/base.py - Already configured in this project
import os

TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', '')
```

Check configuration:

```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.TURNSTILE_SITE_KEY)  # Should print your site key
>>> print(settings.TURNSTILE_SECRET_KEY[:10])  # Print first 10 chars only
```

### 4. Test Integration

1. Start development server: `python manage.py runserver`
2. Visit registration page: `http://127.0.0.1:8000/users/register/`
3. Open browser DevTools → Network tab
4. Submit form and verify:
   - Hidden input `turnstile_token` is populated (Elements tab)
   - POST request to your Django view includes `cf-turnstile-response`
   - View logs show successful verification (check console)

---

## Adding Turnstile to New Forms

### Workflow: Protect Any Django Form

**Step 1: Import and add widget to form**

```python
# myapp/forms.py
from django import forms
from users.turnstile import get_turnstile_widget  # Reuse existing helper

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
    
    # Add Turnstile protection
    turnstile_token = forms.CharField(
        widget=get_turnstile_widget(),
        required=False,  # Graceful degradation
        label=''  # No label needed for CAPTCHA
    )
```

**Step 2: Verify token in view**

```python
# myapp/views.py
from django.shortcuts import render
from users.turnstile import verify_turnstile  # Reuse existing verification
from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Verify Turnstile before processing
            token = form.cleaned_data.get('turnstile_token', '')
            if not verify_turnstile(token, request):
                form.add_error(None, 'Please complete the security check.')
                return render(request, 'contact.html', {'form': form})
            
            # Process form (send email, save to DB, etc.)
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            # ... send email or save to database ...
            
            return render(request, 'contact_success.html')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})
```

**Step 3: Render in template**

```html
<!-- templates/contact.html -->
{% extends 'base.html' %}

{% block content %}
<div class="max-w-2xl mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">Contact Us</h1>
    
    <form method="post">
        {% csrf_token %}
        
        {% if form.non_field_errors %}
        <div class="alert alert-error mb-4">
            {{ form.non_field_errors }}
        </div>
        {% endif %}
        
        <div class="form-control mb-4">
            <label class="label">{{ form.name.label_tag }}</label>
            {{ form.name }}
        </div>
        
        <div class="form-control mb-4">
            <label class="label">{{ form.email.label_tag }}</label>
            {{ form.email }}
        </div>
        
        <div class="form-control mb-4">
            <label class="label">{{ form.message.label_tag }}</label>
            {{ form.message }}
        </div>
        
        <!-- Turnstile widget renders here -->
        {{ form.turnstile_token }}
        
        <button type="submit" class="btn btn-primary">Send Message</button>
    </form>
</div>
{% endblock %}
```

---

## Testing and Debugging

### Test Keys Behavior

Cloudflare provides test keys that always pass or always fail:

**Always Pass (for development):**
```bash
TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
```

**Always Fail (for error handling tests):**
```bash
TURNSTILE_SITE_KEY=2x00000000000000000000AA
TURNSTILE_SECRET_KEY=2x0000000000000000000000000000000AA
```

**Always Block (for testing block scenarios):**
```bash
TURNSTILE_SITE_KEY=3x00000000000000000000AA
TURNSTILE_SECRET_KEY=3x0000000000000000000000000000000AA
```

### Debugging Checklist

When Turnstile isn't working:

- [ ] Check browser console for JavaScript errors
- [ ] Verify widget div has `data-sitekey` attribute with correct key
- [ ] Check Network tab for `siteverify` POST request from server
- [ ] Verify environment variables are loaded: `print(settings.TURNSTILE_SITE_KEY)`
- [ ] Test with test keys first (always pass keys)
- [ ] Check Django logs for verification failures
- [ ] Verify `requests` library is installed: `pip show requests`
- [ ] Test with `curl` directly to Cloudflare API
- [ ] Check Cloudflare Dashboard for request logs (if using real keys)

### Manual API Test

Test verification endpoint directly:

```bash
# Replace with your secret key and a real token
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "1x0000000000000000000000000000000AA",
    "response": "test-token-from-browser"
  }'

# Expected response:
# {"success": true, "challenge_ts": "...", "hostname": "..."}
```

### Logging for Debugging

Add temporary logging to verification function:

```python
# users/turnstile.py
import logging

logger = logging.getLogger(__name__)

def verify_turnstile(token: str, request) -> bool:
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    
    logger.info(f"Turnstile verification: site_key={site_key[:10]}..., token={token[:20]}...")
    
    if not site_key or not secret_key:
        logger.warning("Turnstile keys not configured, allowing through")
        return True
    
    if not token:
        logger.warning("Empty Turnstile token")
        return False
    
    try:
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
        logger.info(f"Turnstile API response: {data}")
        return data.get('success', False)
    except Exception as e:
        logger.error(f"Turnstile verification error: {e}")
        return False
```

Run server with debug logging:

```bash
python manage.py runserver --verbosity 2
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Replace test keys with production keys in environment variables
- [ ] Add production domain to Cloudflare Turnstile site configuration
- [ ] Verify `ALLOWED_HOSTS` includes your production domain
- [ ] Test with production keys in staging environment first
- [ ] Ensure `DEBUG=False` in production settings
- [ ] Verify HTTPS is enforced (Turnstile requires HTTPS in production)
- [ ] Check CSP headers don't block Cloudflare domains
- [ ] Monitor Cloudflare Dashboard for verification rate limits

### Domain Configuration

Update Turnstile site in Cloudflare Dashboard:

1. Visit [Cloudflare Dashboard](https://dash.cloudflare.com/) → Turnstile
2. Select your site
3. Add production domains:
   - `yourdomain.com`
   - `www.yourdomain.com`
   - Any subdomains (e.g., `app.yourdomain.com`)
4. Save changes

### Environment Variables for Production

Set in hosting platform (Heroku, AWS, DigitalOcean, etc.):

```bash
# Via CLI (example for Heroku)
heroku config:set TURNSTILE_SITE_KEY=0x4AAAAAAAY0123456789
heroku config:set TURNSTILE_SECRET_KEY=0x4AAAAAAAY_secretkey_123456789

# Or via hosting dashboard environment variables section
```

### Testing Production Setup

1. Deploy to production/staging
2. Visit form with Turnstile protection
3. Open browser DevTools → Network tab
4. Submit form and verify:
   - Widget loads from `challenges.cloudflare.com`
   - Token is generated and submitted
   - Server logs show successful verification
   - Form submits successfully
5. Check Cloudflare Dashboard → Turnstile → your site → Analytics
   - Verify requests are logged
   - Check pass/fail rates

### Monitoring and Rate Limits

**Cloudflare Free Tier Limits:**
- 1 million requests per month (free)
- No daily limit
- Upgrade to Pro for unlimited requests

**What to Monitor:**
1. **Verification success rate** - Should be >95% (lower means UX issues)
2. **API latency** - Should be <500ms (check timeout logs)
3. **Failed verifications** - Spike may indicate attack or misconfiguration
4. **Monthly quota** - Track requests in Cloudflare Dashboard

### Rollback Plan

If Turnstile causes issues in production:

**Option 1: Disable temporarily**
```bash
# Unset keys - graceful degradation allows forms to work
heroku config:unset TURNSTILE_SITE_KEY
heroku config:unset TURNSTILE_SECRET_KEY
```

**Option 2: Feature flag**
```python
# config/settings/production.py
TURNSTILE_ENABLED = os.environ.get('TURNSTILE_ENABLED', 'true').lower() == 'true'

# users/turnstile.py
def verify_turnstile(token, request):
    if not settings.TURNSTILE_ENABLED:
        return True  # Bypass verification
    # ... normal verification ...