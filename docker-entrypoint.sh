#!/bin/bash
set -e

cd /app/wallpaper_site

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create a superuser if one doesn't exist
echo "Checking for existing superuser..."
SUPERUSER_EXISTS=$(python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wallpaper_site.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).exists())
")

if [ "$SUPERUSER_EXISTS" = "False" ]; then
    echo "No superuser found. Creating a superuser..."
    # Generate a random 16-character password
    ADMIN_PASSWORD=$(openssl rand -base64 12)
    # Create a Python script to create the superuser
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wallpaper_site.settings')
import django
django.setup()
from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@example.com', '$ADMIN_PASSWORD')
"
    echo "========================================================================"
    echo "Superuser created with the following credentials:"
    echo "Username: admin"
    echo "Password: $ADMIN_PASSWORD"
    echo "========================================================================"
else
    echo "Superuser already exists. Skipping creation."
fi

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn wallpaper_site.wsgi:application --workers=8 --bind 0.0.0.0:8000
