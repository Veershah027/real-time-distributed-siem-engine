# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=6
WORKDIR /app

FROM base AS builder
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY pyproject.toml ./
COPY simulator ./simulator
RUN pip install --upgrade pip && pip install .

FROM base AS runtime
RUN groupadd -r sim && useradd -r -g sim -d /app sim
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
COPY --chown=sim:sim simulator ./simulator
COPY --chown=sim:sim pyproject.toml ./
USER sim

ENTRYPOINT ["python", "-m", "simulator"]
CMD []
