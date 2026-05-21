"""Admin routes.

Master Spec §15 Phase 2 acceptance:
  - "Submitting intake reflects correctly in the admin queue with the
    new-lead timestamp."
  - "All intake data round-trips correctly: client enters X, admin reads X."

Phase 2 ships the read-only queue view. Phase 3+ adds the workflow surfaces
(attach reviewer, mark final, release deliverable) on top of this.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_role
from app.models.artifact import Artifact
from app.models.client import Client
from app.models.service_request import ServiceRequest
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminArtifactRow,
    AdminIntakeQueueResponse,
    AdminServiceRequestRow,
    AdminUserSummary,
)
from app.schemas.intake import ClientProfileResponse

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_required = Depends(require_role(UserRole.ADMIN))


@router.get(
    "/intake-queue",
    response_model=AdminIntakeQueueResponse,
    summary="Intake queue (admin)",
)
def intake_queue(
    _admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> AdminIntakeQueueResponse:
    client = db.execute(select(Client).limit(1)).scalar_one_or_none()

    # Pull every service_request with its requester user pre-loaded.
    rows = db.execute(
        select(ServiceRequest, User)
        .join(User, ServiceRequest.requested_by == User.id)
        .order_by(ServiceRequest.requested_at.desc())
    ).all()
    service_requests: list[AdminServiceRequestRow] = []
    for sr, requester in rows:
        service_requests.append(
            AdminServiceRequestRow(
                id=sr.id,
                service_type=sr.service_type,
                requested_at=sr.requested_at,
                requested_by=AdminUserSummary.model_validate(requester, from_attributes=True),
                notes=sr.notes,
                deadline=sr.deadline,
                csf_target_tier=sr.csf_target_tier,
                csf_profile=sr.csf_profile,
                zt_target_stage=sr.zt_target_stage,
                fulfilled_service_id=sr.fulfilled_service_id,
                declined_at=sr.declined_at,
                declined_reason=sr.declined_reason,
            )
        )

    artifact_rows = (
        db.execute(select(Artifact).order_by(Artifact.uploaded_at.desc())).scalars().all()
    )
    artifacts = [AdminArtifactRow.model_validate(a, from_attributes=True) for a in artifact_rows]

    total_users = db.execute(select(func.count()).select_from(User)).scalar_one()

    return AdminIntakeQueueResponse(
        client=(
            ClientProfileResponse.model_validate(client, from_attributes=True)
            if client is not None
            else None
        ),
        intake_completed_at=client.intake_completed_at if client else None,
        service_requests=service_requests,
        artifacts=artifacts,
        total_users=total_users,
    )
