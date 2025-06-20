# Stage 1: Base build stage
FROM python:3.12-slim AS builder

# Create app directory
WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production stage
FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=wallpaper_site.settings

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels

# Copy project
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Create a non-root user to run the application
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
RUN mkdir -p /app/wallpaper_site/static /app/wallpaper_site/staticfiles /app/wallpaper_site/media
RUN chown -R appuser:appuser /app/wallpaper_site/static /app/wallpaper_site/staticfiles /app/wallpaper_site/media

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application
ENTRYPOINT ["/app/docker-entrypoint.sh"]
