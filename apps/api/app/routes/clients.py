"""Client-portal read routes (Sprint 5).

The client-facing surface for released deliverables (Master Spec §6.7, §12).
Tenant-enforced: the `{client_id}` in the path must match the caller's resolved
tenant (client-role users are pinned; platform admins select via X-Client-Id),
and a mismatch 404s — never 403 — so one tenant can't probe another's ids.

Only RELEASED deliverables are ever returned here (§12 release rule): a client
sees nothing until a consultant explicitly releases the finalized deliverable.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import current_client, current_user
from app.logging import get_logger
from app.models.artifact import Artifact
from app.models.client import Client
from app.models.deliverable import Deliverable
from app.models.service import Service
from app.models.user import User
from app.schemas.clients import ClientDeliverableListResponse, ClientDeliverableResponse

router = APIRouter(prefix="/clients", tags=["clients"])

_log = get_logger(__name__)


def _artifact_title(db: Session, artifact_id: uuid.UUID | None) -> str | None:
    if artifact_id is None:
        return None
    art = db.get(Artifact, artifact_id)
    return art.title if art else None


@router.get(
    "/{client_id}/deliverables",
    response_model=ClientDeliverableListResponse,
    summary="Released deliverables for the client (client + admin)",
)
def list_client_deliverables(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    client: Annotated[Client, Depends(current_client)],
    db: Annotated[Session, Depends(get_db)],
) -> ClientDeliverableListResponse:
    # Tenant enforcement: the path id must be the caller's resolved tenant.
    # 404 (never 403) so we don't confirm another tenant's client id exists.
    if client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    rows = (
        db.execute(
            select(Deliverable, Service)
            .join(Service, Service.id == Deliverable.service_id)
            .where(
                Service.client_id == client.id,
                Deliverable.released_at.is_not(None),
            )
            .order_by(Deliverable.released_at.desc())
        )
        .tuples()
        .all()
    )
    _log.info(
        "client.deliverables.listed",
        client_id=str(client.id),
        actor_user_id=str(user.id),
        count=len(rows),
    )

    items = [
        ClientDeliverableResponse(
            id=deliv.id,
            service_id=deliv.service_id,
            service_kind=svc.kind,
            service_title=svc.title,
            title=deliv.title,
            summary=deliv.summary,
            version=deliv.version,
            released_at=deliv.released_at,
            superseded=deliv.superseded_by is not None,
            pdf_artifact_id=deliv.pdf_artifact_id,
            xlsx_artifact_id=deliv.xlsx_artifact_id,
            docx_artifact_id=deliv.docx_artifact_id,
            pdf_filename=_artifact_title(db, deliv.pdf_artifact_id),
            xlsx_filename=_artifact_title(db, deliv.xlsx_artifact_id),
            docx_filename=_artifact_title(db, deliv.docx_artifact_id),
        )
        for deliv, svc in rows
    ]
    return ClientDeliverableListResponse(items=items)
