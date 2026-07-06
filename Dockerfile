# syntax=docker/dockerfile:1

# --- Stage 1: build the React frontend -> frontend/dist ---
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend serving the API + built SPA (single process) ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Install Python dependencies first for layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application source.
COPY . .

# Built SPA from stage 1 (frontend/dist is .dockerignore'd, so copy it in).
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthcheck').status==200 else 1)"
CMD ["python", "main.py"]
