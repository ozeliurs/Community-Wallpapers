#!/bin/bash
set -e

mkdir -p /app/wallpaper_site/media
mkdir -p /app/wallpaper_site/static

# Apply database migrations
echo "Applying database migrations..."
python /app/app/manage.py migrate --noinput

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

python3 /app/app/manage.py runserver 0.0.0.0:8000