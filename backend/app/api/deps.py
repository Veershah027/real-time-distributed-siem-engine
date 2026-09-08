"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.storage.db import get_session
from app.storage.redis_client import get_redis


async def db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def redis_client() -> redis.Redis:
    return get_redis()


DBSession = Annotated[AsyncSession, Depends(db_session)]
RedisClient = Annotated[redis.Redis, Depends(redis_client)]


class Pagination:
    def __init__(
        self,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationDep = Annotated[Pagination, Depends(Pagination)]


async def current_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Returns the caller identity. When auth is disabled, everyone is 'anonymous'."""
    if not settings.auth_enabled:
        return {"sub": "anonymous", "role": "analyst"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )
    claims = decode_access_token(authorization.split(" ", 1)[1])
    return {"sub": claims.get("sub", "unknown"), "role": claims.get("role", "analyst")}


Principal = Annotated[dict[str, str], Depends(current_principal)]
