# Multi-stage build for Node.js dependencies and Tailwind CSS
FROM node:18-alpine AS node-builder
WORKDIR /app/theme/static_src
COPY theme/static_src/package*.json ./
RUN npm ci

# Copy source files needed for Tailwind build
WORKDIR /app
COPY theme/ ./theme/
COPY users/ ./users/
COPY config/ ./config/

# Build Tailwind CSS
WORKDIR /app/theme/static_src
RUN npm run build

# Python base image
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies and clean up in same layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/staticfiles \
    && chown -R app:app /app

# Copy project files
COPY --chown=app:app . .

# Copy built CSS from node-builder stage
COPY --from=node-builder --chown=app:app /app/theme/static/css/dist/ ./theme/static/css/dist/

# Copy node_modules for potential dev use
COPY --from=node-builder --chown=app:app /app/theme/static_src/node_modules ./theme/static_src/node_modules

# Switch to non-root user
USER app

# Collect static files
RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

# Default command (override in docker-compose for production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
