FROM python:3.13-slim
 
RUN mkdir -p /app
WORKDIR /app
 
RUN pip install --upgrade pip 
 
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create the app directory structure with proper permissions
RUN mkdir -p /app/app/media /app/app/static

COPY app /app/app/
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
EXPOSE 8000 
 
ENTRYPOINT ["/app/docker-entrypoint.sh"]
