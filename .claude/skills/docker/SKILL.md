---
name: docker
description: |
  Orchestrates multi-stage Docker builds and docker-compose configurations
  Use when: Setting up local development with Docker, configuring production containers, managing multi-service applications, or ensuring environment parity
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Docker Skill

This Django project uses a **multi-stage Dockerfile** (Python 3.12 + Node.js 18) with **docker-compose profiles** for development and production workflows. The setup provides PostgreSQL and Redis services, replacing SQLite and in-memory caching for production-like local development.

## Quick Start

### Local Development with Docker

```bash
# Basic setup (Django + PostgreSQL + Redis)
docker compose up --build

# With Tailwind development (recommended for frontend work)
docker compose --profile dev up --build

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### Production Build

```bash
# Build production image
export DJANGO_ENV=production
export DEBUG=False
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Key Concepts

| Concept | Usage | Example |
|---------|-------|---------|
| **Multi-stage build** | Python + Node.js in one image | `FROM python:3.12 AS base`, `FROM node:18 AS node` |
| **Compose profiles** | Optional services (Tailwind dev) | `profiles: ["dev"]` |
| **Health checks** | Wait for DB before migrations | `healthcheck: test: ["CMD", "pg_isready"]` |
| **Volume mounts** | Live code reload during development | `./:/app` |
| **Environment files** | Secrets management | `.env.docker` (git-ignored) |

## Common Patterns

### Adding a New Service

**When:** Integrating Celery, Nginx, or other containers

```yaml
# docker-compose.yml
services:
  celery:
    build: .
    command: celery -A config worker -l info
    env_file: .env.docker
    depends_on:
      - redis
      - db
    volumes:
      - ./:/app
```

### Development vs Production Overrides

**When:** Different configurations per environment

```yaml
# docker-compose.prod.yml
services:
  web:
    restart: always
    environment:
      - DJANGO_ENV=production
      - DEBUG=False
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Optimizing Build Cache

**When:** Slow builds from pip installs

```dockerfile
# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code last (changes frequently)
COPY . .
```

## See Also

- [docker](references/docker.md) - Multi-stage builds, compose profiles, volume strategy
- [ci-cd](references/ci-cd.md) - Automated testing and deployment pipelines
- [deployment](references/deployment.md) - Production deployment strategies
- [monitoring](references/monitoring.md) - Container health checks and logging

## Related Skills

- **django** - Framework configuration and Django-specific commands
- **python** - Python runtime and dependency management
- **tailwind** - CSS compilation in Docker (dev profile)
- **postgresql** - Database service configuration
- **redis** - Cache and session storage
- **node-npm** - Node.js integration for Tailwind builds