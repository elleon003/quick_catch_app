# CI/CD Reference

## Contents
- Automated Testing in Docker
- Build Optimization Strategies
- Deployment Pipelines
- Environment-Specific Workflows
- Security Scanning

---

## Automated Testing in Docker

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage pytest-django
      
      - name: Run tests
        env:
          DJANGO_ENV: test
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: test_db
          DB_USER: test_user
          DB_PASSWORD: test_pass
          REDIS_URL: redis://localhost:6379/1
        run: |
          python manage.py migrate
          coverage run manage.py test
          coverage report --fail-under=80
```

**Why services block?** GitHub Actions provides containerized services, avoiding docker-compose in CI.

---

### Pre-commit Hooks for Local CI

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
        language_version: python3.12
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']
  
  - repo: local
    hooks:
      - id: django-test
        name: Django Tests
        entry: docker compose exec -T web python manage.py test
        language: system
        pass_filenames: false
        always_run: true
```

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

**Why local hook for tests?** Ensures tests run in same Docker environment as development.

---

## Build Optimization Strategies

### Layer Caching Strategy

```dockerfile
# GOOD - Optimize for cache hits
FROM python:3.12-slim AS base
WORKDIR /app

# 1. System dependencies (rarely change)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 2. Python dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Node.js setup (change occasionally)
COPY theme/static_src/package*.json theme/static_src/
RUN cd theme/static_src && npm ci

# 4. Application code (changes frequently)
COPY . .
```

**Order matters:** Place least-changed files first to maximize cache reuse.

---

### DON'T: Copy everything then install

```dockerfile
# BAD - Breaks cache on any code change
COPY . .
RUN pip install -r requirements.txt  # Re-runs every time
```

**Why this breaks:** Any code change invalidates the pip install cache, causing full reinstall.

---

### Multi-Architecture Builds

```bash
# Build for both AMD64 and ARM64 (M1/M2 Macs)
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push \
  .
```

**When:** Deploying to AWS Graviton (ARM) or supporting Mac developers.

---

## Deployment Pipelines

### Blue-Green Deployment with Docker

```yaml
# docker-compose.blue.yml
services:
  web-blue:
    image: myapp:v1.2.3
    environment:
      - DJANGO_ENV=production
    networks:
      - frontend

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-blue.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
```

```bash
# Deployment script
#!/bin/bash
set -e

# Deploy green environment
docker compose -f docker-compose.green.yml up -d

# Run health checks
for i in {1..30}; do
  if curl -f http://localhost:8001/health/; then
    echo "Green environment healthy"
    break
  fi
  sleep 2
done

# Switch nginx to green
docker compose exec nginx nginx -s reload

# Stop blue environment
docker compose -f docker-compose.blue.yml down
```

**Why blue-green?** Zero-downtime deployments with instant rollback capability.

---

### Rolling Updates with Health Checks

```yaml
# docker-compose.prod.yml
services:
  web:
    image: myapp:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first  # Start new before stopping old
      rollback_config:
        parallelism: 1
        delay: 5s
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 40s
```

```bash
# Deploy with automatic rollback on failure
docker stack deploy -c docker-compose.prod.yml myapp
```

**Why start-first?** Maintains capacity during deployment, prevents request drops.

---

## Environment-Specific Workflows

### Development Workflow

```bash
# Copy this checklist when starting new feature:
- [ ] Create feature branch: `git checkout -b feature/my-feature`
- [ ] Start dev environment: `docker compose --profile dev up`
- [ ] Make code changes
- [ ] Run tests: `docker compose exec web python manage.py test`
- [ ] Check linting: `docker compose exec web flake8 .`
- [ ] Format code: `docker compose exec web black .`
- [ ] Commit and push
```

**Iterate until tests pass:**
1. Make changes
2. Run `docker compose exec web python manage.py test`
3. If failures, fix and repeat step 2
4. Only commit when all tests pass

---

### Staging Deployment

```yaml
# .github/workflows/staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push to registry
        run: |
          docker build -t registry.example.com/myapp:staging-${GITHUB_SHA} .
          docker push registry.example.com/myapp:staging-${GITHUB_SHA}
      
      - name: Deploy to staging
        env:
          SSH_KEY: ${{ secrets.STAGING_SSH_KEY }}
        run: |
          ssh staging@example.com << EOF
            cd /app
            docker compose pull
            docker compose up -d
            docker compose exec -T web python manage.py migrate
          EOF
```

**Why SHA tagging?** Enables rollback to specific commits, avoids "latest" ambiguity.

---

## Security Scanning

### Scan for Vulnerabilities

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sundays

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

**Why Trivy?** Scans for CVEs in OS packages and Python dependencies.

---

### SECRET SCANNING: Prevent credential leaks

```bash
# Install git-secrets
brew install git-secrets  # macOS
apt-get install git-secrets  # Linux

# Configure for this repo
git secrets --install
git secrets --register-aws
git secrets --add 'SECRET_KEY.*'
git secrets --add 'GOOGLE_CLIENT_SECRET.*'
git secrets --add 'TURNSTILE_SECRET_KEY.*'
```

**The Problem:** Developers accidentally commit `.env.docker` with real secrets.

**The Fix:** Git-secrets prevents commits containing secret patterns.

---

## WARNING: CI/CD Anti-Patterns

### ANTI-PATTERN: Deploying without running migrations

**The Problem:**

```bash
# BAD - Deploy new code without migrating database
docker compose pull && docker compose up -d
```

**Why This Breaks:**
1. **Schema mismatch** - Code expects new columns, database doesn't have them
2. **Runtime errors** - `OperationalError: column does not exist`
3. **Data corruption** - Writes to old schema format

**The Fix:**

```bash
# GOOD - Run migrations before deploying new code
docker compose pull
docker compose run --rm web python manage.py migrate
docker compose up -d
```

**When You Might Be Tempted:** Fast deployments during low traffic, skipping "unnecessary" steps.

---

### ANTI-PATTERN: Building in production

**The Problem:**

```bash
# BAD - Build on production server
ssh production
docker compose build && docker compose up -d
```

**Why This Breaks:**
1. **Slow deployments** - Building takes 5-10 minutes on server
2. **Resource contention** - Build competes with running services
3. **No rollback** - Can't revert to previous build

**The Fix:**

```bash
# GOOD - Build in CI, push to registry
docker build -t registry.example.com/myapp:v1.2.3 .
docker push registry.example.com/myapp:v1.2.3

# Production pulls pre-built image
ssh production
docker compose pull && docker compose up -d
```

**When You Might Be Tempted:** Small projects without CI/CD infrastructure.

---

## See Also

- **docker** reference - Container configuration and multi-stage builds
- **deployment** reference - Production deployment strategies
- **monitoring** reference - Health checks and logging