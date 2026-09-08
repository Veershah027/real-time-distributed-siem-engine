"""Optional dashboard auth (dev seed only).

Active only when ``SIEM_AUTH_ENABLED=true``.  Credentials are seeded from env at
startup for local development; there are no default production credentials.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DBSession, Principal
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: DBSession) -> TokenResponse:
    if not settings.auth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="auth disabled")
    user = await session.scalar(select(User).where(User.username == body.username))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials"
        )
    token = create_access_token(user.username, user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me")
async def me(principal: Principal) -> dict:
    return principal
