"""Health endpoint.

`/health` is the liveness probe used by Docker, Kubernetes, and load
balancers. It does NOT touch downstream dependencies - that's `/ready`,
which will land in Phase 1 stage 2 with the database connection.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

from app import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
