"""Admin routes.

Master Spec §15 Phase 2 acceptance:
  - "Submitting intake reflects correctly in the admin queue with the
    new-lead timestamp."
  - "All intake data round-trips correctly: client enters X, admin reads X."

Phase 2 ships the read-only queue view. Phase 3+ adds the workflow surfaces
(attach reviewer, mark final, release deliverable) on top of this.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import audit
from app.config import get_settings
from app.db.session import get_db
from app.dependencies import require_role
from app.models.artifact import Artifact
from app.models.client import Client
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.service_request import ServiceRequest, ServiceType
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminAiStatus,
    AdminArtifactRow,
    AdminClientCreateRequest,
    AdminClientListResponse,
    AdminClientSummary,
    AdminIntakeQueueResponse,
    AdminServiceDetail,
    AdminServiceRequestRow,
    AdminUserSummary,
    FulfillServiceRequestResponse,
)
from app.schemas.intake import ClientProfileResponse

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_required = Depends(require_role(UserRole.ADMIN))

# Human-readable service titles used when a request graduates to a workspace.
_SERVICE_TITLES: dict[ServiceType, str] = {
    ServiceType.TECH_DEBT: "Technical Debt Review",
    ServiceType.ZERO_TRUST_CISA: "Zero Trust (CISA ZTMM 2.0)",
    ServiceType.ZERO_TRUST_DOD: "Zero Trust (DoD ZTRA)",
    ServiceType.NIST_CSF: "NIST CSF 2.0 Assessment",
    ServiceType.ATTACK_COVERAGE: "MITRE ATT&CK Coverage",
}


@router.get(
    "/intake-queue",
    response_model=AdminIntakeQueueResponse,
    summary="Intake queue (admin)",
)
def intake_queue(
    _admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    client_id: uuid.UUID | None = None,
) -> AdminIntakeQueueResponse:
    """Cross-tenant intake queue.

    Without `client_id` filter: shows requests/artifacts from all clients
    (consultant overview). The `client` field in the response is then the
    most-recently-created tenant for display continuity; treat it as advisory.
    With `client_id`: scopes to that tenant.
    """
    if client_id is not None:
        client = db.get(Client, client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )
    else:
        client = db.execute(
            select(Client).order_by(Client.created_at.desc()).limit(1)
        ).scalar_one_or_none()

    sr_stmt = select(ServiceRequest, User).join(User, ServiceRequest.requested_by == User.id)
    if client_id is not None:
        sr_stmt = sr_stmt.where(ServiceRequest.client_id == client_id)
    sr_stmt = sr_stmt.order_by(ServiceRequest.requested_at.desc())
    rows = db.execute(sr_stmt).all()
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

    art_stmt = select(Artifact)
    if client_id is not None:
        art_stmt = art_stmt.where(Artifact.client_id == client_id)
    art_stmt = art_stmt.order_by(Artifact.uploaded_at.desc())
    artifact_rows = db.execute(art_stmt).scalars().all()
    artifacts = [AdminArtifactRow.model_validate(a, from_attributes=True) for a in artifact_rows]

    user_stmt = select(func.count()).select_from(User)
    if client_id is not None:
        user_stmt = user_stmt.where(User.client_id == client_id)
    total_users = db.execute(user_stmt).scalar_one()

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


@router.get(
    "/clients",
    response_model=AdminClientListResponse,
    summary="List all clients (admin/reviewer)",
)
def list_clients(
    _admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> AdminClientListResponse:
    rows = (
        db.execute(select(Client).order_by(Client.created_at.desc()))
        .scalars()
        .all()
    )
    return AdminClientListResponse(
        clients=[AdminClientSummary.model_validate(r, from_attributes=True) for r in rows]
    )


@router.post(
    "/clients",
    response_model=AdminClientSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client tenant (admin)",
)
def create_client(
    body: AdminClientCreateRequest,
    admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> AdminClientSummary:
    legal_name = body.legal_name.strip()
    if not legal_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="legal_name is required.",
        )
    client = Client(
        legal_name=legal_name,
        dba_name=body.dba_name,
        industry=body.industry,
        size_band=body.size_band,
    )
    db.add(client)
    db.flush()
    audit(
        db,
        action="client.created",
        target_type="client",
        target_id=client.id,
        actor_user_id=admin.id,
        details={"legal_name": legal_name, "source": "admin"},
    )
    db.commit()
    db.refresh(client)
    return AdminClientSummary.model_validate(client, from_attributes=True)


@router.get(
    "/clients/{cid}",
    response_model=AdminClientSummary,
    summary="Client detail (admin/reviewer)",
)
def get_client(
    cid: uuid.UUID,
    _admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> AdminClientSummary:
    client = db.get(Client, cid)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )
    return AdminClientSummary.model_validate(client, from_attributes=True)


@router.post(
    "/service-requests/{request_id}/fulfill",
    response_model=FulfillServiceRequestResponse,
    summary="Publish a service request for processing (admin)",
)
def fulfill_service_request(
    request_id: uuid.UUID,
    admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> FulfillServiceRequestResponse:
    """Graduate a service request into a live engagement workspace.

    The admin reviews the client's inputs + uploads in the queue, then
    publishes: this opens the Service (status in_progress) so the consultant
    can run the assessment and the AI pipeline against vetted intake data.
    Idempotent — re-publishing returns the existing workspace.
    """
    sr = db.get(ServiceRequest, request_id)
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )
    if sr.service_type == ServiceType.CONSULTATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation requests are handled directly, not published as a service.",
        )
    if sr.fulfilled_service_id is not None:
        existing = db.get(Service, sr.fulfilled_service_id)
        if existing is not None:
            return FulfillServiceRequestResponse(
                service_id=existing.id,
                service_type=sr.service_type,
                title=existing.title,
                already_fulfilled=True,
            )

    client = db.get(Client, sr.client_id)
    org = client.legal_name if client is not None else "Client"
    svc = Service(
        kind=ServiceKind(sr.service_type.value),
        status=ServiceStatus.IN_PROGRESS,
        title=f"{org} — {_SERVICE_TITLES[sr.service_type]}",
        client_id=sr.client_id,
        source_request_id=sr.id,
        opened_by=admin.id,
    )
    db.add(svc)
    db.flush()
    sr.fulfilled_service_id = svc.id
    audit(
        db,
        action="service_request.fulfilled",
        target_type="service",
        target_id=svc.id,
        actor_user_id=admin.id,
        details={"service_type": sr.service_type.value, "request_id": str(sr.id)},
    )
    db.commit()
    db.refresh(svc)
    return FulfillServiceRequestResponse(
        service_id=svc.id,
        service_type=sr.service_type,
        title=svc.title,
        already_fulfilled=False,
    )


@router.get(
    "/services/{service_id}",
    response_model=AdminServiceDetail,
    summary="Service detail (admin) - resolves a workspace's owning tenant",
)
def get_service(
    service_id: uuid.UUID,
    _admin: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> AdminServiceDetail:
    """Look up a service by id, including its client_id.

    Cross-tenant on purpose (admin-only, no X-Client-Id): the workspace UI
    calls this to discover which client a service belongs to, then sets that
    as the active tenant before its tenant-scoped data calls.
    """
    svc = db.get(Service, service_id)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )
    return AdminServiceDetail.model_validate(svc, from_attributes=True)


@router.get(
    "/ai-status",
    response_model=AdminAiStatus,
    summary="AI pipeline readiness (admin)",
)
def ai_status(_admin: Annotated[User, _admin_required]) -> AdminAiStatus:
    """Report whether AI features will actually run a live call.

    `ready` is true only when a real provider call will be made. Fixture mode
    (and live mode missing its key) report ready=false with a reason. The API
    key itself is never returned.
    """
    s = get_settings()
    mode = s.shield_llm_mode
    provider = s.shield_llm_provider
    model = s.shield_llm_model

    if mode != "live":
        return AdminAiStatus(
            mode=mode,
            provider=provider,
            model=model,
            ready=False,
            detail=(
                "Running in fixture mode — AI features are disabled. Set "
                "SHIELD_LLM_MODE=live and ANTHROPIC_API_KEY to enable."
            ),
        )
    if provider == "anthropic" and not s.anthropic_api_key:
        return AdminAiStatus(
            mode=mode,
            provider=provider,
            model=model,
            ready=False,
            detail="Live mode is on but ANTHROPIC_API_KEY is not set.",
        )
    return AdminAiStatus(
        mode=mode,
        provider=provider,
        model=model,
        ready=True,
        detail=f"Live AI configured ({provider}/{model}).",
    )
