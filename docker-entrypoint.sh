#!/bin/bash
set -e

# Create required directories
mkdir -p /app/app/media
mkdir -p /app/app/media/wallpapers
mkdir -p /app/app/static

# Set working directory to properly find modules
cd /app/app

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Checking for existing superuser..."
SUPERUSER_EXISTS=$(cd /app/app && python -c "
import os
import sys
sys.path.append('/app/app')
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
    cd /app/app && python -c "
import os
import sys
sys.path.append('/app/app')
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

# Start Django development server
python manage.py runserver 0.0.0.0:8000
