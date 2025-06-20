FROM python:3.13-slim
 
RUN mkdir -p /app
WORKDIR /app
 
RUN pip install --upgrade pip 
 
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create the app directory structure with proper permissions
RUN mkdir -p /app/app/media /app/app/static && \
    useradd -m -r appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser app /app/app/
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
USER appuser
 
EXPOSE 8000 
 
ENTRYPOINT ["/app/docker-entrypoint.sh"]