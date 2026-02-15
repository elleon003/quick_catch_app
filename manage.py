#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings

# Suppress multiprocessing resource_tracker leak warning on shutdown when running
# "tailwind dev" (Django + Tailwind watcher). Child processes exit on Ctrl+C
# without cleaning semaphores; harmless but noisy.
if len(sys.argv) >= 3 and sys.argv[1] == "tailwind" and sys.argv[2] == "dev":
    warnings.filterwarnings(
        "ignore",
        message=r".*resource_tracker.*leaked.*",
        category=UserWarning,
        module="multiprocessing.resource_tracker",
    )


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
