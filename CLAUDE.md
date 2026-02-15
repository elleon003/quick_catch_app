# Django Starter Template

A production-ready Django starter template with modern authentication, social login, magic links, Tailwind CSS styling, and comprehensive security features. Built for rapid development with best practices baked in.

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Runtime | Python | 3.12+ | Modern Python with performance improvements |
| Framework | Django | 5.2.x | Full-featured web framework with admin panel |
| Frontend | Tailwind CSS | 4.x | Utility-first CSS framework with new v4 syntax |
| UI Components | DaisyUI | 5.x | Pre-built Tailwind component library |
| Database (Dev) | SQLite | - | Zero-config development database |
| Database (Prod) | PostgreSQL | 15+ | Production-grade relational database |
| Cache | Redis | 7.x | Session storage and caching (production) |
| Auth | Django Social Auth | 5.6.x | Google and LinkedIn OAuth2 integration |
| Magic Links | Django Sesame | 3.2.x | One-time passwordless authentication |
| CAPTCHA | Cloudflare Turnstile | - | Bot protection for forms |
| API | Django Ninja | 1.5.x | Modern API framework (FastAPI-style, newly added) |

## Quick Start

### Prerequisites
- Python 3.8 or higher (3.12+ recommended)
- Node.js 18+ and npm (for Tailwind CSS compilation)
- Git

### Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd ygitc-django-starter

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Tailwind dependencies
python manage.py tailwind install

# Set up environment variables
cp .env.example .env
# Edit .env with your OAuth/Turnstile keys if needed

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server (Django + Tailwind)
python manage.py tailwind dev
```

Visit http://127.0.0.1:8000/ to see your application.

### Docker Development

```bash
# Set up environment variables (same file works for local and Docker)
cp .env.example .env
# Edit .env with your OAuth/Turnstile keys if needed

# Start all services (Django + PostgreSQL + Redis)
docker compose up --build

# Start with Tailwind development (recommended for frontend work)
docker compose --profile dev up --build

# Run migrations in Docker
docker compose exec web python manage.py migrate

# Create superuser in Docker
docker compose exec web python manage.py createsuperuser
```

Visit http://localhost:8000 to see your application.

## Project Structure

```
ygitc-django-starter/
├── config/                     # Project configuration
│   ├── settings/               # Split settings architecture
│   │   ├── __init__.py        # Settings loader (loads dotenv, checks DJANGO_ENV)
│   │   ├── base.py            # Shared settings for all environments
│   │   ├── development.py     # Development-specific (SQLite, DEBUG=True)
│   │   └── production.py      # Production-specific (PostgreSQL, security)
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point (async support)
│
├── users/                      # Custom authentication app
│   ├── models.py              # CustomUser (email-based auth)
│   ├── auth_models.py         # AuthProvider, AuthLinkingToken (multi-auth tracking)
│   ├── forms.py               # Registration and login forms with Turnstile
│   ├── views.py               # Auth views (register, login, magic link, etc.)
│   ├── turnstile.py           # Cloudflare Turnstile integration
│   ├── urls.py                # User-related URLs
│   └── admin.py               # User admin configuration
│
├── theme/                      # UI theme and styling
│   ├── templates/             # Django templates
│   │   ├── base.html          # Base layout template
│   │   ├── home.html          # Landing page
│   │   ├── dashboard.html     # User dashboard
│   │   ├── user_settings.html # User settings page
│   │   ├── partials/          # Reusable components (_header.html, _footer.html)
│   │   ├── registration/      # Auth templates (login.html, register.html)
│   │   ├── users/             # User-specific templates (auth_settings.html)
│   │   └── examples/          # Template examples (different layouts)
│   ├── static_src/            # Tailwind source files
│   │   ├── src/styles.css     # Tailwind v4 CSS config (CSS-based, not JS)
│   │   ├── package.json       # Node.js dependencies
│   │   └── postcss.config.js  # PostCSS configuration
│   └── static/                # Compiled static files
│
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Multi-stage Python 3.12 + Node.js 18 build
├── .env.example               # Environment template (works for local and Docker)
├── README.md                  # Full project documentation
└── CLAUDE.md                  # This file
```

## Architecture Overview

This project uses Django's standard MVT (Model-View-Template) architecture with a split settings pattern for environment-specific configuration. Authentication is handled through a custom user model with email as the primary identifier, supporting multiple authentication methods: traditional email/password, social OAuth2 (Google, LinkedIn), and magic links.

**Key Design Decisions:**

- **Split Settings**: Separate configuration files for base, development, and production environments enable secure defaults and easy deployment. Settings are loaded via `config/settings/__init__.py` which checks the `DJANGO_ENV` environment variable.
- **Custom User Model**: Email-based authentication instead of username provides better UX and aligns with modern practices.
- **Multi-Auth Strategy**: Traditional, social, and passwordless authentication options offer flexibility for different user preferences. The `AuthProvider` model tracks which authentication methods each user has connected.
- **Tailwind CSS v4**: Uses new CSS-first configuration in `styles.css` with `@import`, `@source`, and `@plugin` directives. No `tailwind.config.js` file required.
- **DaisyUI Components**: Pre-built component library enables rapid UI development without custom CSS.
- **Docker-Ready**: Multi-stage Dockerfile and compose configuration support both development and production workflows.

**Authentication Flow:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Login    │────▶│  Auth Provider  │────▶│   CustomUser    │
│ (Password/OAuth)│◀────│   Validation    │◀────│  (Email-based)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        │                        ▼                        ▼
        │               ┌─────────────────┐     ┌─────────────────┐
        └──────────────▶│  AuthProvider   │     │    Database     │
                        │  Model (tracks) │────▶│ (SQLite/Postgres)│
                        └─────────────────┘     └─────────────────┘
```

### Key Modules

| Module | Location | Purpose |
|--------|----------|---------|
| **CustomUser** | users/models.py:32 | Email-based user model with first/last name fields |
| **CustomUserManager** | users/models.py:5 | Manager for creating users and superusers with email |
| **AuthProvider** | users/auth_models.py:5 | Tracks multiple authentication methods per user (email, google, linkedin, magic_link) |
| **AuthLinkingToken** | users/auth_models.py:35 | Manages temporary tokens for linking auth providers to existing accounts |
| **Turnstile Integration** | users/turnstile.py | Cloudflare CAPTCHA verification and configuration |
| **Settings Loader** | config/settings/__init__.py | Loads python-dotenv and determines environment via DJANGO_ENV |
| **Settings Base** | config/settings/base.py | Shared configuration for all environments |
| **Settings Development** | config/settings/development.py | SQLite, DEBUG mode, console email backend |
| **Settings Production** | config/settings/production.py | PostgreSQL, Redis cache, HTTPS enforcement |

## Development Guidelines

### File and Code Naming Conventions

**File naming (Python standard):**
- Python modules: `snake_case.py` (e.g., `user_settings.py`, `auth_models.py`)
- Django apps: lowercase single words or snake_case (e.g., `users`, `theme`)
- Templates: snake_case with `.html` extension (e.g., `user_settings.html`)
- Partials: Leading underscore for reusable components (e.g., `_header.html`, `_footer.html`)

**Code naming:**
- Class names: `PascalCase` (e.g., `CustomUser`, `AuthProvider`)
- Function names: `snake_case` with descriptive verbs (e.g., `register_view`, `verify_turnstile`)
- Variable names: `snake_case` (e.g., `user_settings`, `magic_link`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `LOGIN_REDIRECT_URL`, `SESAME_MAX_AGE`)
- Django view functions: suffix with `_view` (e.g., `login_view`, `dashboard_view`)
- Boolean variables: Use `is_`, `has_`, `should_` prefix (e.g., `is_authenticated`, `has_permission`)

### Import Order

Follow PEP 8 import ordering:
1. Standard library imports (e.g., `import os`, `from datetime import datetime`)
2. Django core imports (e.g., `from django.shortcuts import render`, `from django.contrib.auth.models import AbstractBaseUser`)
3. Third-party imports (e.g., `from social_django.models import UserSocialAuth`, `import requests`)
4. Local application imports (e.g., `from .forms import CustomUserCreationForm`, `from .models import CustomUser`)

### Template Patterns

- All templates extend `base.html` using `{% extends 'base.html' %}`
- Use `{% block content %}` for main content area
- Additional blocks: `{% block title %}`, `{% block extra_css %}`, `{% block extra_js %}`
- Partials stored in `theme/templates/partials/` for reusable components
- Load static files with `{% load static %}` at the top of templates
- Use DaisyUI components for consistent UI (buttons, forms, cards, modals)
- See examples in `theme/templates/examples/` for different layout patterns

### Authentication Patterns

- Always use `@login_required` decorator for protected views
- Access current user via `request.user` in views or `{{ user }}` in templates
- Check authentication status with `request.user.is_authenticated`
- Social auth URLs are automatically configured via `social_django.urls`
- Magic links generated with `from sesame.utils import get_token; token = get_token(user)`
- AuthProvider model tracks which methods user has used: `AuthProvider.objects.filter(user=user)`

## Available Commands

### Development Server

| Command | Description |
|---------|-------------|
| `python manage.py tailwind dev` | Start both Django server and Tailwind watcher (recommended) |
| `python manage.py runserver` | Start Django development server only (port 8000) |
| `python manage.py tailwind start` | Start Tailwind watcher only (for CSS changes) |

### Database Operations

| Command | Description |
|---------|-------------|
| `python manage.py makemigrations` | Create new database migrations from model changes |
| `python manage.py migrate` | Apply pending migrations to database |
| `python manage.py createsuperuser` | Create admin user for Django admin panel |
| `python manage.py dbshell` | Open database shell (SQLite or PostgreSQL) |
| `python manage.py showmigrations` | Show migration status for all apps |

### Static Files & Frontend

| Command | Description |
|---------|-------------|
| `python manage.py tailwind install` | Install Node.js dependencies for Tailwind |
| `python manage.py tailwind build` | Build production-optimized CSS |
| `python manage.py collectstatic` | Collect all static files to STATIC_ROOT (production) |

### Utilities

| Command | Description |
|---------|-------------|
| `python manage.py shell` | Django shell for interactive Python/Django testing |
| `python manage.py check` | Check for common Django project issues |
| `pip-review` | Check for outdated packages (pip-review installed) |
| `pip-review --interactive` | Interactively update packages |

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker compose up --build` | Start basic services (web, db, redis) |
| `docker compose --profile dev up --build` | Start with Tailwind development |
| `docker compose exec web python manage.py migrate` | Run migrations in Docker |
| `docker compose exec web python manage.py createsuperuser` | Create superuser in Docker |
| `docker compose logs -f web` | Follow Django application logs |
| `docker compose down` | Stop all services |

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key for cryptographic signing | 50-character random string |
| `DEBUG` | Enable debug mode (True/False) | `False` for production |
| `DJANGO_ENV` | Environment to use (development/production) | `production` |

**Note:** `DJANGO_ENV` is checked by `config/settings/__init__.py` to determine which settings module to load. Defaults to `development` if not set.

### Optional Variables

**Database (defaults to SQLite in development):**
| Variable | Description | Example |
|----------|-------------|---------|
| `DB_ENGINE` | Database backend | `django.db.backends.postgresql` |
| `DB_NAME` | Database name | `mydatabase` |
| `DB_USER` | Database user | `myuser` |
| `DB_PASSWORD` | Database password | `securepassword` |
| `DB_HOST` | Database host | `localhost` or `db` (Docker) |
| `DB_PORT` | Database port | `5432` |

**Email Configuration (required for magic links):**
| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP server host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_HOST_USER` | SMTP username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | Use app-specific password for Gmail |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@yourdomain.com` |

**OAuth Providers:**
| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID | [Google Cloud Console](https://console.cloud.google.com/) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret | Google Cloud Console |
| `LINKEDIN_CLIENT_ID` | LinkedIn OAuth2 client ID | [LinkedIn Developer Portal](https://www.linkedin.com/developers/) |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn OAuth2 client secret | LinkedIn Developer Portal |

**CAPTCHA Protection:**
| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key | [Cloudflare Dashboard](https://dash.cloudflare.com/) |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret key | Cloudflare Dashboard |

**Other Settings:**
| Variable | Description | Example |
|----------|-------------|---------|
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `yourdomain.com,www.yourdomain.com` |
| `TIME_ZONE` | Django timezone | `America/New_York` |
| `REDIS_URL` | Redis connection URL (production) | `redis://localhost:6379/1` |

### Environment File Setup

A single `.env` file works for both local and Docker development:

```bash
cp .env.example .env
# Edit .env with your settings
```

Docker Compose automatically overrides host-specific values (DB_HOST, REDIS_URL) so the same `.env` file works in both environments.

**Test Turnstile keys for development:**
- **Site Key**: `1x00000000000000000000AA`
- **Secret Key**: `1x0000000000000000000000000000000AA`

**Note:** `.env` is git-ignored to prevent committing credentials.

## Authentication Features

### Available Authentication Methods

1. **Traditional Email/Password**: Standard Django authentication with email as username
2. **Google OAuth2**: One-click login with Google account
3. **LinkedIn OAuth2**: Professional network authentication
4. **Magic Links**: Passwordless email-based one-time login (via django-sesame)

**Multi-Auth Support:** Users can connect multiple authentication methods to a single account. The `AuthProvider` model tracks which methods are linked to each user.

### URL Structure

| URL | View | Purpose | Auth Required |
|-----|------|---------|---------------|
| `/` | `home_view` | Landing page | No |
| `/users/register/` | `register_view` | User registration with CAPTCHA | No |
| `/users/login/` | `login_view` | User login with CAPTCHA | No |
| `/users/logout/` | `logout_view` | User logout | No |
| `/users/dashboard/` | `dashboard_view` | User dashboard | Yes |
| `/users/settings/` | `user_settings_view` | User settings and auth management | Yes |
| `/users/magic/<token>/` | `magic_login_view` | Magic link login (one-time use) | No |
| `/complete/google-oauth2/` | Social auth | Google OAuth callback | No |
| `/complete/linkedin-oauth2/` | Social auth | LinkedIn OAuth callback | No |
| `/admin/` | Django admin | Admin panel | Superuser |

### Social Authentication Setup

**Google OAuth2:**
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable Google+ API or Google Identity API
3. Create OAuth 2.0 Client ID (Web application)
4. Add authorized redirect URIs:
   - Development: `http://localhost:8000/complete/google-oauth2/`
   - Production: `https://yourdomain.com/complete/google-oauth2/`
5. Copy Client ID and Client Secret to environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)

**LinkedIn OAuth2:**
1. Visit [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create new application
3. In "Auth" tab, add redirect URLs:
   - Development: `http://localhost:8000/complete/linkedin-oauth2/`
   - Production: `https://yourdomain.com/complete/linkedin-oauth2/`
4. Request access to "Sign In with LinkedIn" product
5. Copy Client ID and Client Secret to environment variables (`LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`)

**Cloudflare Turnstile:**
1. Visit [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to Turnstile section and create new site
3. Add domain (`localhost` for development)
4. Choose "Managed" challenge type
5. Copy Site Key and Secret Key to environment variables (`TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`)

### Magic Link Configuration

Magic links provide passwordless authentication via django-sesame:

**Settings** (config/settings/base.py):
- `SESAME_MAX_AGE = 3600` (1 hour expiration)
- `SESAME_ONE_TIME = True` (single-use tokens)
- Authentication backend: `sesame.backends.ModelBackend`

**Sending Magic Links:**
```python
from sesame.utils import get_token
from django.urls import reverse

token = get_token(user)
magic_url = request.build_absolute_uri(reverse('magic_login', args=[token]))
# Send magic_url via email to user
```

**URL:** `/users/magic/<token>/` - User clicks link, gets logged in automatically

## Testing

This project follows Django's standard testing conventions:

- **Test files**: Located in each app directory as `tests.py` (or `tests/` directory)
- **Test classes**: Inherit from `django.test.TestCase`
- **Run all tests**: `python manage.py test`
- **Run specific app tests**: `python manage.py test users`
- **Run with coverage**: Install `coverage` and use `coverage run manage.py test`

**Recommended tests to add:**
- User registration and login flows
- Social authentication integration
- Magic link generation and validation
- Custom user model functionality
- AuthProvider model and multi-auth tracking
- Template rendering and context
- Turnstile CAPTCHA integration

**Current state:** Test infrastructure in place, but no comprehensive test suite yet. Test files exist (e.g., `users/tests.py`) but are mostly empty.

## Deployment

### Production Checklist

1. **Set production environment**:
   ```bash
   export DJANGO_ENV=production
   export DEBUG=False
   ```

2. **Configure environment variables**: Set all required variables in `.env` or hosting platform

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Build production CSS**:
   ```bash
   python manage.py tailwind build
   ```

7. **Create superuser** (if needed):
   ```bash
   python manage.py createsuperuser
   ```

### Production Security Features (Automatic)

When using `config.settings.production` (or `DJANGO_ENV=production`), these security features are automatically enabled:

- `SECURE_SSL_REDIRECT=True` - Force HTTPS
- `SESSION_COOKIE_SECURE=True` - Cookies only over HTTPS
- `CSRF_COOKIE_SECURE=True` - CSRF protection over HTTPS
- `SECURE_HSTS_SECONDS=31536000` - Enforce HTTPS for 1 year
- `SECURE_BROWSER_XSS_FILTER=True` - Enable browser XSS protection
- `SECURE_CONTENT_TYPE_NOSNIFF=True` - Prevent MIME sniffing

### Docker Deployment

For production Docker deployment, create a `docker-compose.prod.yml` override file or use environment variables:

```bash
export DJANGO_ENV=production
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Docker Services:**
- **db**: PostgreSQL 15 with health checks
- **redis**: Redis 7-alpine for caching and session storage
- **web**: Django application (Python 3.12 + Node.js 18 multi-stage build)
- **tailwind** (dev profile): CSS compilation with live reload

## Adding New Features

### Creating a New Django App

```bash
# Create new app
python manage.py startapp myapp

# Add to INSTALLED_APPS in config/settings/base.py
INSTALLED_APPS = [
    # ... existing apps ...
    'myapp',
]

# Create models in myapp/models.py
# Create views in myapp/views.py
# Create templates in theme/templates/myapp/
# Create URL patterns in myapp/urls.py

# Include URLs in config/urls.py
urlpatterns = [
    # ... existing patterns ...
    path('myapp/', include('myapp.urls')),
]

# Make migrations and apply
python manage.py makemigrations myapp
python manage.py migrate
```

### Customizing Styles

**Tailwind CSS v4 Configuration:**
1. **Edit CSS config**: `theme/static_src/src/styles.css` (uses new v4 syntax with `@import`, `@source`, `@plugin` directives)
2. **No tailwind.config.js needed**: Tailwind v4 uses CSS-based configuration
3. **PostCSS plugins**: Configure in `theme/static_src/postcss.config.js`
4. **Add custom CSS**: Use CSS layers: `@layer utilities { ... }`, `@layer components { ... }`
5. **Use DaisyUI themes**: Change `data-theme` attribute in templates (light, dark, synthwave, etc.)
6. **Component library**: Browse [DaisyUI components](https://daisyui.com/components/)

**Tailwind v4 Features:**
- Content scanning via `@source` directive: `@source "../../../**/*.{html,py,js}"`
- Plugin loading via `@plugin` directive: `@plugin "@tailwindcss/forms"`
- Theme configuration in CSS: `@theme { ... }`

## Important Files and Locations

| Purpose | Path | Description |
|---------|------|-------------|
| Settings loader | config/settings/__init__.py | Loads python-dotenv and checks DJANGO_ENV |
| Base configuration | config/settings/base.py | Shared settings for all environments |
| Development settings | config/settings/development.py | SQLite, DEBUG mode, console email |
| Production settings | config/settings/production.py | PostgreSQL, Redis, security features |
| User model | users/models.py | CustomUser (line 32), CustomUserManager (line 5) |
| Auth models | users/auth_models.py | AuthProvider (line 5), AuthLinkingToken (line 35) |
| Auth views | users/views.py | All authentication views including magic link |
| Turnstile utils | users/turnstile.py | CAPTCHA verification functions |
| Main URLs | config/urls.py | Root URL configuration |
| User URLs | users/urls.py | User-specific URL patterns |
| Templates | theme/templates/ | All HTML templates (base, partials, registration) |
| Template examples | theme/templates/examples/ | Example layouts (with/without header/footer) |
| Tailwind v4 config | theme/static_src/src/styles.css | CSS-based Tailwind configuration |
| PostCSS config | theme/static_src/postcss.config.js | PostCSS plugin configuration |
| Node deps | theme/static_src/package.json | Frontend dependencies (Tailwind, DaisyUI, etc.) |
| Python deps | requirements.txt | Backend dependencies |
| Docker compose | docker-compose.yml | Container orchestration |
| Dockerfile | Dockerfile | Multi-stage Python 3.12 + Node.js 18 build |
| Env template | .env.example | Environment variable template (works for local and Docker) |

## Known Issues and Notes

1. **Django Ninja API Framework**: Django Ninja (1.5.x) is installed but not yet configured. No API endpoints exist yet. Add API routes when needed for RESTful endpoints.

2. **Production Dependencies**: Production settings reference packages not in requirements.txt:
   - `whitenoise` - For serving static files without a separate web server
   - `django-redis` - For Redis cache backend
   - Add these to requirements.txt before production deployment if needed

3. **Single Environment File**: A single `.env` file works for both local and Docker development. Docker Compose overrides host-specific values automatically.

4. **Test Suite**: Test infrastructure exists but no comprehensive test suite is implemented yet. Test files exist (e.g., `users/tests.py`) but are mostly empty placeholders. Implement tests before production use.

5. **Tailwind CSS v4**: This project uses the new Tailwind CSS v4 with CSS-based configuration. If you're familiar with v3's JavaScript config file (`tailwind.config.js`), note that v4 uses `@theme`, `@source`, and `@plugin` directives in CSS instead.

6. **Package Management**: `pip-review` is included in requirements.txt for easy package updates. Run `pip-review --interactive` to update dependencies.

## AI Assistant Configuration

### Context7 MCP Integration

This project uses Context7 MCP to provide up-to-date library documentation during development. Context7 automatically fetches current documentation, code examples, and API references for any library in the tech stack.

**When Context7 is used:**
- Library/API documentation lookups
- Code generation requiring current syntax
- Setup and configuration steps
- Troubleshooting library-specific issues

**Supported libraries include:**
- Django 5.2.x
- Tailwind CSS 4.x
- DaisyUI 5.x
- Django Social Auth
- Django Sesame
- Django Ninja
- PostgreSQL
- Redis

**Usage:** Context7 is invoked automatically when documentation or code generation assistance is needed - no explicit request required.

## Additional Resources

- **Full Project Documentation**: See @README.md for detailed setup and configuration
- **Django Documentation**: https://docs.djangoproject.com/
- **Tailwind CSS v4**: https://tailwindcss.com/docs
- **DaisyUI Components**: https://daisyui.com/
- **Django Social Auth**: https://python-social-auth.readthedocs.io/
- **Django Sesame (Magic Links)**: https://django-sesame.readthedocs.io/
- **Cloudflare Turnstile**: https://developers.cloudflare.com/turnstile/
- **Django Ninja**: https://django-ninja.dev/

---

**Built with Django 5.2, Tailwind CSS 4, and modern web development best practices.**
