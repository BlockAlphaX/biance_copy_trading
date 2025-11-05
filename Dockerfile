# Multi-stage build for production

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY web/frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source
COPY web/frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-web.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-web.txt

# Copy application code
COPY src/ ./src/
COPY web/ ./web/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY main.py main_futures.py web_server.py ./

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/dist ./web/frontend/dist

# Create necessary directories
RUN mkdir -p logs data

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/status')"

# Run the application
CMD ["python", "web_server.py"]
