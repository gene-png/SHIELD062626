"""Client-facing deliverable routes (Phase 3 stage 9).

Admin-facing finalize/release/latest live under `/tech-debt/`. These
routes give the engagement's CLIENT users a read-only view of released
deliverables across all service kinds. Single-tenant deployments (§2)
mean every CLIENT user sees every released deliverable for the
singleton client.

Visibility rules:
  - role=admin / reviewer : see every deliverable (released or not)
  - role=client           : see only deliverables whose
                            released_to_client_at IS NOT NULL
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import current_user
from app.models.artifact import Artifact
from app.models.deliverable import Deliverable
from app.models.service import Service
from app.models.user import User, UserRole
from app.schemas.tech_debt import DeliverableResponse

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


class DeliverableListItem(BaseModel):
    """Shape returned by the client list endpoint.

    Lighter than DeliverableResponse so the client view doesn't pull in
    fields it can't act on (finalized_by, superseded_by).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    service_title: str
    title: str
    summary: str | None
    version: int
    pdf_artifact_id: uuid.UUID | None
    xlsx_artifact_id: uuid.UUID | None
    pdf_filename: str | None
    xlsx_filename: str | None
    released_to_client_at: str | None


class DeliverableListResponse(BaseModel):
    items: list[DeliverableListItem]


def _filenames(db: Session, deliv: Deliverable) -> tuple[str | None, str | None]:
    pdf = None
    xlsx = None
    if deliv.pdf_artifact_id:
        art = db.get(Artifact, deliv.pdf_artifact_id)
        pdf = art.title if art else None
    if deliv.xlsx_artifact_id:
        art = db.get(Artifact, deliv.xlsx_artifact_id)
        xlsx = art.title if art else None
    return pdf, xlsx


def _is_visible_to(user: User, deliv: Deliverable) -> bool:
    if user.role == UserRole.ADMIN or user.role == UserRole.REVIEWER:
        return True
    return deliv.released_to_client_at is not None


@router.get(
    "",
    response_model=DeliverableListResponse,
    summary="List deliverables visible to the current user",
)
def list_deliverables(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableListResponse:
    stmt = select(Deliverable, Service).join(Service, Service.id == Deliverable.service_id)
    if user.role == UserRole.CLIENT:
        stmt = stmt.where(Deliverable.released_to_client_at.is_not(None))
    # Hide superseded versions in the list; admins can still fetch them
    # by ID via the detail endpoint for audit.
    stmt = stmt.where(Deliverable.superseded_by.is_(None))
    stmt = stmt.order_by(Deliverable.released_to_client_at.desc().nullslast(),
                         Deliverable.finalized_at.desc().nullslast())
    rows = db.execute(stmt).all()
    items: list[DeliverableListItem] = []
    for deliv, svc in rows:
        pdf, xlsx = _filenames(db, deliv)
        items.append(
            DeliverableListItem(
                id=deliv.id,
                service_id=svc.id,
                service_title=svc.title,
                title=deliv.title,
                summary=deliv.summary,
                version=deliv.version,
                pdf_artifact_id=deliv.pdf_artifact_id,
                xlsx_artifact_id=deliv.xlsx_artifact_id,
                pdf_filename=pdf,
                xlsx_filename=xlsx,
                released_to_client_at=deliv.released_to_client_at.isoformat()
                if deliv.released_to_client_at
                else None,
            )
        )
    return DeliverableListResponse(items=items)


@router.get(
    "/{deliverable_id}",
    response_model=DeliverableResponse,
    summary="Deliverable detail (client-safe view)",
)
def deliverable_detail(
    deliverable_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse:
    deliv = db.get(Deliverable, deliverable_id)
    if deliv is None or not _is_visible_to(user, deliv):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deliverable not found.",
        )
    pdf, xlsx = _filenames(db, deliv)
    return DeliverableResponse(
        id=deliv.id,
        service_id=deliv.service_id,
        title=deliv.title,
        summary=deliv.summary,
        version=deliv.version,
        pdf_artifact_id=deliv.pdf_artifact_id,
        xlsx_artifact_id=deliv.xlsx_artifact_id,
        pdf_filename=pdf,
        xlsx_filename=xlsx,
        finalized_at=deliv.finalized_at,
        finalized_by=deliv.finalized_by,
        released_to_client_at=deliv.released_to_client_at,
        superseded_by=deliv.superseded_by,
    )
