#!/bin/bash
set -e

cd /app/wallpaper_site

# Wait for the database to be ready (if using PostgreSQL or MySQL)
# Uncomment the following if you're using a separate database service
# until nc -z $DATABASE_HOST $DATABASE_PORT; do
#     echo "Waiting for database at $DATABASE_HOST:$DATABASE_PORT..."
#     sleep 2
# done
# echo "Database is available!"

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

# Set up cron job for image of the day (if needed)
# Uncomment and modify if you need cron jobs
# echo "Setting up cron job for Image of the Day..."
# echo "0 0 * * * cd /app/wallpaper_site && python manage.py select_image_of_the_day >> /var/log/cron.log 2>&1" > /tmp/crontab
# crontab /tmp/crontab
# rm /tmp/crontab
# service cron start

# Start Gunicorn server with optimal settings
echo "Starting Gunicorn server..."
exec gunicorn wallpaper_site.wsgi:application \
    --workers=$(( 2 * $(nproc) )) \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    --capture-output
