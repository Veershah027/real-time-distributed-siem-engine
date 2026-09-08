"""Simulator control endpoints — drive demos from the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import Principal, RedisClient
from app.services.simulator_control import (
    SCENARIOS,
    get_status,
    set_state,
)

router = APIRouter()


class SimulatorConfig(BaseModel):
    rate: int | None = Field(None, ge=0, le=20_000, description="events per second")
    scenario: str | None = Field(None)
    attack_ratio: float | None = Field(None, ge=0.0, le=1.0)
    burst: bool | None = None


@router.get("/status")
async def status(redis: RedisClient) -> dict:
    return await get_status(redis)


@router.get("/scenarios")
async def scenarios() -> dict:
    return {"scenarios": SCENARIOS}


@router.post("/start")
async def start(
    redis: RedisClient, principal: Principal, cfg: SimulatorConfig | None = None
) -> dict:
    patch: dict = {"running": True}
    if cfg:
        patch.update({k: v for k, v in cfg.model_dump().items() if v is not None})
    if "scenario" in patch and patch["scenario"] not in SCENARIOS:
        raise HTTPException(status_code=422, detail=f"unknown scenario: {patch['scenario']}")
    state = await set_state(redis, patch, actor=principal["sub"])
    return {"ok": True, "desired": state}


@router.post("/stop")
async def stop(redis: RedisClient, principal: Principal) -> dict:
    state = await set_state(redis, {"running": False}, actor=principal["sub"])
    return {"ok": True, "desired": state}


@router.post("/configure")
async def configure(cfg: SimulatorConfig, redis: RedisClient, principal: Principal) -> dict:
    patch = {k: v for k, v in cfg.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=422, detail="no configuration supplied")
    if "scenario" in patch and patch["scenario"] not in SCENARIOS:
        raise HTTPException(status_code=422, detail=f"unknown scenario: {patch['scenario']}")
    state = await set_state(redis, patch, actor=principal["sub"])
    return {"ok": True, "desired": state}
