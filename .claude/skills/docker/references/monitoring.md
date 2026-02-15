# Monitoring Reference

## Contents
- Health Check Endpoints
- Container Logging
- Performance Metrics
- Error Tracking
- Alerting Strategies

---

## Health Check Endpoints

### Django Health Check View

```python
# users/views.py or create health/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """
    Health check endpoint for load balancers and monitoring.
    Returns 200 if all systems operational, 503 otherwise.
    """
    checks = {}
    
    # Database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
    
    # Cache connectivity (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['cache'] = 'ok'
        else:
            checks['cache'] = 'error: cache write/read failed'
    except Exception as e:
        checks['cache'] = f'error: {str(e)}'
    
    # Check if any service failed
    all_ok = all(status == 'ok' for status in checks.values())
    status_code = 200 if all_ok else 503
    
    return JsonResponse({
        'status': 'healthy' if all_ok else 'unhealthy',
        'checks': checks,
    }, status=status_code)
```

```python
# config/urls.py
urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ... other patterns
]
```

**Why 503 on failure?** Load balancers remove unhealthy instances from rotation.

---

### Docker Health Checks

```yaml
# docker-compose.yml
services:
  web:
    image: myapp:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s      # Check every 30 seconds
      timeout: 10s       # Fail if response takes >10s
      retries: 3         # Mark unhealthy after 3 failures
      start_period: 40s  # Grace period on startup
```

```bash
# Check container health status
docker compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' myapp_web_1 | jq
```

**Why start_period?** Migrations take time on startup; prevents false unhealthy status.

---

## Container Logging

### Structured Logging Configuration

```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',  # Use 'verbose' for development
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',  # Log 500 errors
            'propagate': False,
        },
    },
}
```

**Why JSON logs?** Easy parsing by log aggregators (ELK, Datadog, CloudWatch).

---

### Viewing Logs

```bash
# Follow all container logs
docker compose logs -f

# Follow specific service
docker compose logs -f web

# Last 100 lines from web service
docker compose logs --tail=100 web

# Filter by timestamp
docker compose logs --since 2024-01-01T10:00:00 web

# Search logs for errors
docker compose logs web | grep ERROR
```

---

### Centralized Logging with Fluent Bit

```yaml
# docker-compose.prod.yml
services:
  web:
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: django.web
  
  fluentbit:
    image: fluent/fluent-bit:latest
    ports:
      - "24224:24224"
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
```

```ini
# fluent-bit.conf
[INPUT]
    Name forward
    Port 24224

[OUTPUT]
    Name es
    Match django.*
    Host elasticsearch
    Port 9200
    Index django-logs
```

**Why Fluent Bit?** Lightweight log forwarder to Elasticsearch, CloudWatch, or Datadog.

---

## Performance Metrics

### Django Request Metrics

```python
# Custom middleware for request timing
# config/middleware.py
import time
import logging

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        logger.info(
            'Request completed',
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration * 1000,
            }
        )
        
        return response
```

```python
# config/settings/base.py
MIDDLEWARE = [
    'config.middleware.RequestTimingMiddleware',  # Add at top
    # ... other middleware
]
```

**Why custom middleware?** Tracks slow endpoints, helps identify performance bottlenecks.

---

### Database Query Monitoring

```python
# config/settings/development.py
LOGGING = {
    # ... existing config
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',  # Log all SQL queries
            'handlers': ['console'],
        },
    },
}
```

**WARNING:** Never enable SQL logging in production (performance impact + sensitive data).

---

### Prometheus Metrics (Optional)

```python
# Install: pip install django-prometheus

# config/settings/base.py
INSTALLED_APPS = [
    'django_prometheus',
    # ... other apps
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

```yaml
# docker-compose.yml
services:
  web:
    ports:
      - "8000:8000"
      - "8001:8001"  # Prometheus metrics endpoint
```

**Metrics exposed at:** `http://localhost:8001/metrics`

**Includes:** Request latency, request count, database query time, cache hit rate.

---

## Error Tracking

### Sentry Integration

```bash
# Install Sentry SDK
pip install sentry-sdk
```

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    environment='production',
    traces_sample_rate=0.1,  # 10% of requests for performance monitoring
    send_default_pii=False,  # Don't send user IPs, emails
)
```

**Why Sentry?** Aggregates errors, shows stack traces, tracks affected users.

---

### Custom Error Logging

```python
# users/views.py
import logging

logger = logging.getLogger(__name__)

def register_view(request):
    try:
        # ... registration logic
        pass
    except Exception as e:
        logger.exception(
            'Registration failed',
            extra={
                'user_email': request.POST.get('email'),
                'ip_address': request.META.get('REMOTE_ADDR'),
            }
        )
        # Show user-friendly error
        return render(request, 'registration/error.html')
```

**Why logger.exception?** Includes full stack trace in logs for debugging.

---

## Alerting Strategies

### Basic Health Check Monitoring

```bash
#!/bin/bash
# health-monitor.sh - Run as cron job

URL="https://yourdomain.com/health/"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ "$STATUS" -ne 200 ]; then
    echo "ALERT: Health check failed with status $STATUS" | \
        mail -s "Production Down" ops@example.com
fi
```

**Cron schedule:** `*/5 * * * * /path/to/health-monitor.sh`

---

### Uptime Monitoring Services

**External monitors (recommended):**
- **UptimeRobot** - Free, checks every 5 minutes
- **Pingdom** - Detailed performance metrics
- **Better Uptime** - Incident management

**Configuration:**
1. Monitor `https://yourdomain.com/health/`
2. Alert on 3 consecutive failures
3. Check from multiple regions

---

### Log-Based Alerting

```yaml
# CloudWatch Logs metric filter
FilterPattern: "[timestamp, request_id, level=ERROR, ...]"

# Alert when error rate > 10/minute
Alarm:
  MetricName: ErrorCount
  Threshold: 10
  Period: 60
  EvaluationPeriods: 1
```

**Why metric filters?** Detect error spikes before users report issues.

---

## WARNING: Monitoring Anti-Patterns

### ANTI-PATTERN: No health checks

**The Problem:**

```yaml
# BAD - No health check configured
services:
  web:
    image: myapp:latest
    ports:
      - "8000:8000"
```

**Why This Breaks:**
1. **No visibility** - Container appears running but Django crashed
2. **Load balancer issues** - Routes traffic to broken instances
3. **Slow incident detection** - Users report issues before ops team knows

**The Fix:**

```yaml
# GOOD - Health check with proper intervals
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### ANTI-PATTERN: Logging sensitive data

**The Problem:**

```python
# BAD - Logs contain passwords, tokens
logger.info(f"User login: {email}, password: {password}")
logger.debug(f"OAuth token: {access_token}")
```

**Why This Breaks:**
1. **Security violation** - Credentials in log aggregators
2. **Compliance issues** - GDPR, PCI-DSS violations
3. **Audit failures** - Exposes sensitive data to ops team

**The Fix:**

```python
# GOOD - Redact sensitive fields
logger.info(f"User login attempt: {email}")
logger.debug(f"OAuth token: {'*' * 10}{access_token[-4:]}")  # Last 4 chars only
```

---

## See Also

- **docker** reference - Container health checks and logging configuration
- **deployment** reference - Production deployment with monitoring
- **ci-cd** reference - Automated health checks in pipelines