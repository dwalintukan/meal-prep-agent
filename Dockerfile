# syntax=docker/dockerfile:1

# Python backend serving the API only. The React SPA is built and hosted
# separately on Vercel (app.forkcast.app); see frontend/vercel.json.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend
WORKDIR /app/backend

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/backend/.venv/bin:$PATH"

# Install Python dependencies first for layer caching.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Backend source.
COPY backend/ ./

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthcheck').status==200 else 1)"
CMD ["python", "main.py"]
