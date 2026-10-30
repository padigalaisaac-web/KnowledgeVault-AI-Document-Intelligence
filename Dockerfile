# ============================================================
# KnowledgeVault AI — Self-Extracting Production Dockerfile
# Optimized for Render, Railway, Fly.io, and Local Docker Runs
# Supports both loose folders and zipped repo distributions
# ============================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Install unzip in case source is packaged as KnowledgeVault-AI-Production.zip
RUN apk add --no-cache unzip

COPY . .

# If source is packed in zip and frontend folder is not extracted, unpack it
RUN if [ -f "KnowledgeVault-AI-Production.zip" ] && [ ! -d "frontend/src" ]; then \
        unzip -q -o KnowledgeVault-AI-Production.zip; \
    fi

WORKDIR /build/frontend
RUN npm ci
RUN npm run build

# --- Stage 2: Install Python Dependencies ---
FROM python:3.11-slim AS python-builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN if [ -f "KnowledgeVault-AI-Production.zip" ] && [ ! -f "backend/requirements.txt" ]; then \
        unzip -q -o KnowledgeVault-AI-Production.zip; \
    fi

WORKDIR /build/backend
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 3: Production Runtime ---
FROM python:3.11-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from Stage 2
COPY --from=python-builder /install /usr/local

# Copy application files (or unpack from zip)
COPY . /app

RUN if [ -f "/app/KnowledgeVault-AI-Production.zip" ] && [ ! -d "/app/backend/app" ]; then \
        unzip -q -o /app/KnowledgeVault-AI-Production.zip -d /app; \
    fi

# Copy compiled frontend distribution from Stage 1
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

# Ensure persistent directories exist
RUN mkdir -p /app/data/uploads /app/data/vector_storage

# Environment configuration
ENV PYTHONPATH=/app/backend:/app \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000 10000

# Health check probing Render's dynamic $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/health || exit 1

# Start Uvicorn dynamically on the port assigned by Render ($PORT)
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
