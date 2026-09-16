# syntax=docker/dockerfile:1

# One image: FastAPI serves the built SPA + the API + the committed DuckDB on $PORT.

# 1) Build the Vue SPA -> /web/dist
FROM node:24-slim AS web
WORKDIR /web
COPY app/web/package.json app/web/package-lock.json ./
RUN npm ci
COPY app/web/ ./
RUN npm run build

# 2) Python runtime (uv) that serves everything
FROM python:3.14-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Runtime deps only (cached on the lockfile)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# App code + the committed dataset; SPA from the web stage
COPY pyproject.toml ./
COPY pipeline/ ./pipeline/
COPY app/__init__.py ./app/
COPY app/api/ ./app/api/
COPY config/ ./config/
COPY data/db/atlas.duckdb ./data/db/atlas.duckdb
COPY --from=web /web/dist ./app/web/dist

ENV PATH="/app/.venv/bin:$PATH"
# Cloud Run sets $PORT (default 8080); shell form so it expands.
CMD python -m uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
