"""HTTP security: request IDs, security headers, Redis-backed rate limiting,
and optional JWT auth for the dashboard (dev-seed only).
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import structlog
from fastapi import HTTPException, Request, status
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.storage.redis_client import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id", "path")
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.1f}"
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window limiter keyed by client IP, backed by Redis (fails open)."""

    def __init__(self, app: Any, limit_per_minute: int | None = None) -> None:
        super().__init__(app)
        self.limit = limit_per_minute or settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"siem:ratelimit:{client_ip}:{window}"
        try:
            r = get_redis()
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, 90)
            if current > self.limit:
                return Response(
                    content='{"error":"rate_limited","detail":"too many requests"}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={"Retry-After": "60", **SECURITY_HEADERS},
                )
        except Exception:  # noqa: BLE001 - never let the limiter take the API down
            pass
        return await call_next(request)


# --------------------------------------------------------------------------- #
# JWT helpers (only used when settings.auth_enabled)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, role: str = "analyst") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "iss": settings.service_name,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.service_name
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        ) from exc
