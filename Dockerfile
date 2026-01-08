FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (minimal)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements/base.txt /requirements/base.txt
COPY requirements/ai.txt /requirements/ai.txt
COPY requirements/analytics.txt /requirements/analytics.txt

# Upgrade pip + install deps (separate layers for better caching)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /requirements/base.txt && \
    pip install --no-cache-dir -r /requirements/ai.txt && \
    pip install --no-cache-dir -r /requirements/analytics.txt

# Copy application code
COPY app/ ./app/

# Create directories for data
RUN mkdir -p exports charts/generated cache

# Expose port
EXPOSE 3300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3300/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3300"]
