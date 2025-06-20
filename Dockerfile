FROM python:3.13-slim
 
RUN mkdir /app
WORKDIR /app
 
RUN pip install --upgrade pip 
 
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -r appuser && \
   chown -R appuser /app
 
COPY --chown=appuser:appuser . .
 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
USER appuser
 
EXPOSE 8000 
 
ENTRYPOINT ["/app/docker-entrypoint.sh"]