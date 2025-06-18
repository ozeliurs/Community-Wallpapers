#!/bin/bash
set -e

cd /app/wallpaper_site

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn wallpaper_site.wsgi:application --bind 0.0.0.0:8000
