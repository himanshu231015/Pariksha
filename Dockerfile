# ==============================================================================
# Pariksha - Production Dockerfile
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (build-essential for psycopg2, libpq-dev, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media/protected/papers \
    /app/media/protected/contributions \
    /app/media/protected/syllabus \
    /app/media/protected/solutions \
    /app/media/avatars \
    /app/staticfiles

# Expose standard port
EXPOSE 8000

# Default command: Start Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "config.wsgi:application"]
