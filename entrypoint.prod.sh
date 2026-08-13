#!/bin/bash
set -e  # stop on errors

# Run Django management commands
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Start Gunicorn
exec gunicorn DWLR.wsgi:application --bind 0.0.0.0:8000 --workers 3


