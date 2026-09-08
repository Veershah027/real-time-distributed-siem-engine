from fastapi import APIRouter

from app.api.routes import (
    alerts,
    auth,
    detections,
    events,
    health,
    metrics,
    realtime,
    simulator,
    system,
    threats,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(events.router, prefix="/api/events", tags=["events"])
api_router.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
api_router.include_router(metrics.router, prefix="/api", tags=["metrics"])
api_router.include_router(threats.router, prefix="/api/threats", tags=["threats"])
api_router.include_router(detections.router, prefix="/api/detections", tags=["detections"])
api_router.include_router(system.router, prefix="/api/system", tags=["system"])
api_router.include_router(simulator.router, prefix="/api/simulator", tags=["simulator"])
api_router.include_router(auth.router, prefix="/api/auth", tags=["auth"])
api_router.include_router(realtime.router, tags=["realtime"])
