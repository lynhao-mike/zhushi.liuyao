# =============================================================================
# Multi-stage Dockerfile for zhushi-liuyao API
# =============================================================================
# Stage 1 — builder  : install all deps, including build tools
# Stage 2 — runtime  : minimal image with only runtime artifacts
# =============================================================================

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System build deps (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specs first (layer-cache friendly)
COPY pyproject.toml ./
COPY requirements.txt ./

# Install into a prefix so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="zhushi-liuyao"
LABEL description="六爻 divination analysis API"

WORKDIR /app

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY liuyao/       ./liuyao/
COPY api/          ./api/
COPY migrations/   ./migrations/
COPY alembic.ini   ./

# Ensure the non-root user owns everything
RUN chown -R appuser:appgroup /app

USER appuser

# Expose the API port
EXPOSE 8000

# Health check — used by Docker Compose / K8s
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default: run Uvicorn in production mode
# Override CMD in docker-compose for dev (--reload)
CMD ["uvicorn", "api.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "warning"]
