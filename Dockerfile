# ============================================================
# KnowledgeVault AI — Unified Multi-Stage Production Dockerfile
# Optimized for Render, Railway, Fly.io, and Local Docker Runs
# ============================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Install Python Dependencies ---
FROM python:3.11-slim AS python-builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 3: Production Runtime ---
FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages
COPY --from=python-builder /install /usr/local

# Copy backend application
COPY backend/app /app/backend/app
COPY backend/pyproject.toml /app/backend/pyproject.toml

# Copy compiled frontend distribution
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy seed datasets and sample documents
COPY data/benchmark_dataset.json /app/data/benchmark_dataset.json
COPY data/sample_documents /app/data/sample_documents

# Ensure persistent directories exist
RUN mkdir -p /app/data/uploads /app/data/vector_storage

# Environment configuration
ENV PYTHONPATH=/app/backend:/app \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000 10000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/health || exit 1

# Start Uvicorn dynamically on the port assigned by Render ($PORT)
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
