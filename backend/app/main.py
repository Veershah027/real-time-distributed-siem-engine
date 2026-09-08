"""FastAPI application factory."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import __version__
from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import REGISTRY
from app.core.security import RateLimitMiddleware, RequestContextMiddleware
from app.storage.db import dispose_engine, get_sessionmaker
from app.storage.redis_client import close_redis, get_redis

log = get_logger("api")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log.info("api_starting", version=__version__, env=settings.env)
    get_sessionmaker()
    get_redis()
    if settings.auth_enabled:
        with contextlib.suppress(Exception):
            await _seed_admin()
    yield
    await close_redis()
    await dispose_engine()
    log.info("api_stopped")


async def _seed_admin() -> None:
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.models import User
    from app.storage.db import session_scope

    async with session_scope() as session:
        existing = await session.scalar(
            select(User).where(User.username == settings.seed_admin_username)
        )
        if existing is None:
            session.add(
                User(
                    username=settings.seed_admin_username,
                    password_hash=hash_password(settings.seed_admin_password),
                    role="admin",
                )
            )
            log.warning(
                "seeded_dev_admin",
                username=settings.seed_admin_username,
                note="development credentials — change before any shared deployment",
            )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Real-Time Distributed Enterprise SIEM Engine",
        version=__version__,
        description=(
            "Ingestion, event streaming, real-time detection, anomaly analysis, "
            "alert correlation, and live security analytics. Portfolio-grade "
            "educational platform — see README limitations."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "service": "siem-engine",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/metrics", include_in_schema=False)
    async def metrics_exposition() -> Response:
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        log.error("unhandled_exception", error=str(exc), path=request.url.path)
        detail = str(exc) if not settings.is_production else "internal server error"
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detail": detail, "request_id": request_id},
        )

    return app


app = create_app()
