# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# --- build layer: resolve + install dependencies into a venv ---
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
# install runtime deps only (no dev/ml extras) from pyproject
RUN pip install --upgrade pip && pip install .

# --- runtime image ---
FROM base AS runtime
RUN groupadd -r siem && useradd -r -g siem -d /app siem
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --chown=siem:siem app ./app
COPY --chown=siem:siem alembic ./alembic
COPY --chown=siem:siem alembic.ini pyproject.toml ./
COPY --chown=siem:siem scripts ./scripts
RUN chmod +x /app/scripts/entrypoint.sh

USER siem
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status==200 else 1)" || exit 1

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["api"]
