"""Liveness + readiness endpoints.

`/health` is the liveness probe (process is up).
`/ready` is the readiness probe (process can serve traffic - DB reachable).
Load balancers may point at either; orchestrators (k8s) use both.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.db.session import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    version: str
    checks: dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness probe (touches downstream dependencies)",
)
def ready(db: Session = Depends(get_db)) -> ReadyResponse:  # noqa: B008 - FastAPI DI idiom
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "ok"
        overall = "ok"
    except Exception as exc:  # noqa: BLE001 - readiness deliberately broad
        checks["db"] = f"down: {type(exc).__name__}"
        overall = "degraded"
    return ReadyResponse(status=overall, version=__version__, checks=checks)
