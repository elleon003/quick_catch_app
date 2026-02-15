# Docker Reference

## Contents
- Multi-Stage Dockerfile Strategy
- docker-compose Configuration
- Volume Mounting Patterns
- Environment Variable Management
- Common Anti-Patterns
- Troubleshooting

---

## Multi-Stage Dockerfile Strategy

This project uses **Python 3.12 + Node.js 18** in a single image for Tailwind CSS compilation:

```dockerfile
# Stage 1: Node.js for Tailwind
FROM node:18 AS node

# Stage 2: Python base
FROM python:3.12-slim AS base
WORKDIR /app

# Copy Node.js from Stage 1
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/bin/npm /usr/local/bin/npm

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (changes frequently)
COPY . .

# Install Tailwind dependencies
RUN python manage.py tailwind install

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Why multi-stage?** Avoids bloating the final image with Node.js build tools while keeping Tailwind compilation functional.

---

## docker-compose Configuration

### Service Dependencies with Health Checks

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${DB_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    env_file: .env.docker
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
```

**Why `condition: service_healthy`?** Prevents Django from attempting migrations before PostgreSQL is ready, avoiding connection errors.

---

### Compose Profiles for Optional Services

```yaml
services:
  tailwind:
    build: .
    command: python manage.py tailwind start
    profiles: ["dev"]  # Only runs with --profile dev
    volumes:
      - ./:/app
```

**Usage:**
```bash
# Without Tailwind (faster startup)
docker compose up

# With Tailwind live reload
docker compose --profile dev up
```

**Why profiles?** Production doesn't need Tailwind watcher; profiles keep the default setup minimal.

---

## Volume Mounting Patterns

### DO: Mount entire project for live reload

```yaml
services:
  web:
    volumes:
      - ./:/app  # Live code changes reflected immediately
```

### DON'T: Mount system directories

```yaml
# WRONG - Overwrites container's installed packages
volumes:
  - ./:/usr/local/lib/python3.12/site-packages
```

**Why this breaks:** Overwrites pip-installed packages with empty host directories, causing import errors.

---

### Named Volumes for Persistent Data

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:  # Named volume persists across container rebuilds
```

**Why named volumes?** Database data survives `docker compose down` and rebuilds.

---

## Environment Variable Management

### DO: Use .env.docker (git-ignored)

```bash
# .env.docker.example (committed template)
SECRET_KEY=CHANGEME
DEBUG=True
GOOGLE_CLIENT_ID=your-google-client-id
TURNSTILE_SITE_KEY=your-turnstile-site-key

# .env.docker (git-ignored, real secrets)
SECRET_KEY=actual-secret-key
GOOGLE_CLIENT_SECRET=actual-secret
```

```yaml
# docker-compose.yml
services:
  web:
    env_file: .env.docker  # Loads all variables
```

**Workflow:**
1. Copy `.env.docker.example` to `.env.docker`
2. Edit `.env.docker` with real secrets
3. Never commit `.env.docker`

---

### DON'T: Hardcode secrets in docker-compose.yml

```yaml
# WRONG - Secrets committed to git
services:
  web:
    environment:
      - SECRET_KEY=django-insecure-hardcoded-key
      - GOOGLE_CLIENT_SECRET=actual-secret
```

**Why this breaks:** Secrets leak into version control, security vulnerability.

**The fix:** Use `env_file` and git-ignore the secrets file.

---

## WARNING: Common Anti-Patterns

### ANTI-PATTERN: Running migrations in Dockerfile

**The Problem:**

```dockerfile
# BAD - Migrations run during image build
RUN python manage.py migrate
```

**Why This Breaks:**
1. **Build-time vs runtime** - Database isn't available during `docker build`
2. **Immutable images** - Bakes migrations into image, can't be rolled back
3. **Deployment race conditions** - Multiple containers run migrations simultaneously

**The Fix:**

```bash
# GOOD - Run migrations as a separate step after containers start
docker compose exec web python manage.py migrate
```

Or use an init container:

```yaml
services:
  migrate:
    build: .
    command: python manage.py migrate
    depends_on:
      db:
        condition: service_healthy
    restart: "no"  # Run once, don't restart
```

**When You Might Be Tempted:** Trying to automate the deployment process by including migrations in the image build.

---

### ANTI-PATTERN: Using latest tags in production

**The Problem:**

```yaml
# BAD - Unpredictable behavior
services:
  db:
    image: postgres:latest
```

**Why This Breaks:**
1. **Breaking changes** - `latest` can introduce incompatible updates
2. **Non-reproducible builds** - Same compose file produces different results over time
3. **Rollback issues** - Can't revert to previous "latest"

**The Fix:**

```yaml
# GOOD - Pin specific versions
services:
  db:
    image: postgres:15.6
  redis:
    image: redis:7.2-alpine
```

**When You Might Be Tempted:** During initial development when you "just want it to work."

---

### ANTI-PATTERN: Root user in production

**The Problem:**

```dockerfile
# BAD - Runs as root by default
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Why This Breaks:**
1. **Security risk** - Container escape = root on host
2. **File permission issues** - Files created as root:root
3. **Compliance violations** - Fails security audits

**The Fix:**

```dockerfile
# GOOD - Create and switch to non-root user
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**When You Might Be Tempted:** Development environments where permissions "just work" as root.

---

## Troubleshooting

### Database Connection Refused

**Symptom:** `django.db.utils.OperationalError: could not connect to server`

**Diagnosis:**
```bash
# Check if database is ready
docker compose exec db pg_isready -U postgres

# Check logs
docker compose logs db
```

**Fix:** Add health check to docker-compose.yml (shown above).

---

### Tailwind CSS Not Compiling

**Symptom:** Styles not updating in browser

**Diagnosis:**
```bash
# Check if tailwind service is running
docker compose ps

# Check tailwind logs
docker compose logs tailwind
```

**Fix:** Ensure using dev profile:
```bash
docker compose --profile dev up
```

---

### Volume Permission Errors

**Symptom:** `PermissionError: [Errno 13] Permission denied`

**Cause:** Host user UID ≠ container user UID

**Fix:**
```dockerfile
# Match container user UID to host user UID
ARG USER_UID=1000
RUN useradd -m -u ${USER_UID} django
USER django
```

```bash
# Build with host UID
docker compose build --build-arg USER_UID=$(id -u)
```

---

## See Also

- **django** skill - Django-specific management commands
- **postgresql** skill - Database configuration and optimization
- **redis** skill - Cache backend setup
- **deployment** reference - Production deployment strategies