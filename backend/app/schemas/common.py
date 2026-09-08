"""Shared API schemas: pagination, errors, health."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    env: str
    checks: dict[str, str] = Field(default_factory=dict)
