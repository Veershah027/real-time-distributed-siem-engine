"""Real-time transports: WebSocket (primary) and SSE (fallback).

Both bridge Redis pub/sub channels (events, alerts, metrics) to the browser.
The dashboard updates with no polling.
"""

from __future__ import annotations

import asyncio
import contextlib

import orjson
from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from sse_starlette.sse import EventSourceResponse

from app.core.logging import get_logger
from app.storage.redis_client import (
    CHANNEL_ALERTS,
    CHANNEL_EVENTS,
    CHANNEL_METRICS,
    get_redis,
)

router = APIRouter()
log = get_logger("api.realtime")

_CHANNELS = {
    "events": CHANNEL_EVENTS,
    "alerts": CHANNEL_ALERTS,
    "metrics": CHANNEL_METRICS,
}


def _resolve_channels(topics: str | None) -> list[str]:
    if not topics:
        return list(_CHANNELS.values())
    picked = [
        _CHANNELS[t.strip()] for t in topics.split(",") if t.strip() in _CHANNELS
    ]
    return picked or list(_CHANNELS.values())


@router.websocket("/ws")
async def ws(websocket: WebSocket, topics: str | None = Query(None)) -> None:
    await websocket.accept()
    channels = _resolve_channels(topics)
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(*channels)
    await websocket.send_json({"type": "connected", "channels": channels})

    async def _pump_client() -> None:
        # Drain (and ignore) client pings so disconnects are detected promptly.
        with contextlib.suppress(WebSocketDisconnect):
            while True:
                await websocket.receive_text()

    client_task = asyncio.create_task(_pump_client())
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            channel = message["channel"]
            kind = next((k for k, v in _CHANNELS.items() if v == channel), "unknown")
            data = message["data"]
            try:
                payload = orjson.loads(data)
            except (orjson.JSONDecodeError, TypeError):
                payload = {"raw": data}
            await websocket.send_json({"type": kind, "data": payload})
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        log.warning("ws_error", error=str(exc))
    finally:
        client_task.cancel()
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()


@router.get("/sse")
async def sse(request: Request, topics: str | None = Query(None)) -> EventSourceResponse:
    channels = _resolve_channels(topics)
    redis = get_redis()

    async def event_gen():
        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=15
                )
                if message is None:
                    yield {"event": "ping", "data": "{}"}
                    continue
                channel = message["channel"]
                kind = next((k for k, v in _CHANNELS.items() if v == channel), "unknown")
                yield {"event": kind, "data": message["data"]}
        finally:
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(*channels)
                await pubsub.aclose()

    return EventSourceResponse(event_gen())
