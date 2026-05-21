"""Intake routes.

Master Spec §15 Phase 2:
  - Six-step wizard with auto-save on blur.
  - Pre-fill from authenticated session everywhere possible (email,
    display name).
  - Service selection drives downstream pages.
  - Admin notification fires on intake submit (Phase 2 stage 8 - wired
    once notification infrastructure lands; this stage just emits the
    audit row, which the queue surfaces by querying it).
  - All copy in plain English (UI concern; API returns structured data).

Single-tenant deployments have exactly one `client` row (Master Spec §2).
GET /intake/me upserts that row on first call so the wizard always has a
target to PATCH against. Subsequent PATCH/submit operate on the same row.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import audit
from app.db.session import get_db
from app.dependencies import current_user
from app.models._common import utcnow
from app.models.client import Client
from app.models.service_request import ServiceRequest, ServiceType
from app.models.user import User, UserRole
from app.notifications import notify_role
from app.schemas.intake import (
    IntakePatchRequest,
    IntakeStateResponse,
    IntakeSubmitRequest,
    ServiceRequestInput,
)

_ZT_SERVICE_TYPES = (ServiceType.ZERO_TRUST_CISA, ServiceType.ZERO_TRUST_DOD)


def _validate_targets(item: ServiceRequestInput) -> None:
    """Enforce client-supplied assessment targets per selected service.

    The wizard gates this in the UI, but we re-check server-side so the
    target is never silently dropped (the consultant relies on it).
    """
    if item.service_type == ServiceType.NIST_CSF:
        if item.csf_target_tier is None or item.csf_profile is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="NIST CSF requires a target tier and profile before submitting.",
            )
    elif item.service_type in _ZT_SERVICE_TYPES:
        if item.zt_target_stage is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Zero Trust requires a target stage before submitting.",
            )

router = APIRouter(prefix="/intake", tags=["intake"])


def _singleton_client(db: Session) -> Client:
    """Return the deployment's singleton client row, creating it if missing.

    Per Master Spec §2 (single-tenant), there is exactly one client per
    deployment. The first call to /intake creates a placeholder so the
    wizard's auto-save can PATCH it without a separate "create" step.
    """
    row = db.execute(select(Client).limit(1)).scalar_one_or_none()
    if row is None:
        row = Client(legal_name="(pending intake)")
        db.add(row)
        db.flush()
    return row


def _apply_patch_to_client(client: Client, patch: IntakePatchRequest) -> None:
    if patch.client is None:
        return
    data = patch.client.model_dump(exclude_unset=True)
    if "website" in data and data["website"] is not None:
        data["website"] = str(data["website"])
    if "service_interests" in data and data["service_interests"] is not None:
        data["service_interests"] = [v.value for v in data["service_interests"]]
    for field, value in data.items():
        setattr(client, field, value)


def _apply_profile_fields(user: User, fields: dict[str, str | None]) -> None:
    """Apply only the profile fields present in `fields` AND non-None.

    Caller is responsible for filtering down to set-and-non-None values so
    we don't overwrite a stored timezone with None just because the caller
    didn't include it (which would violate the NOT NULL on users.timezone).
    """
    for field, value in fields.items():
        if value is None:
            continue
        setattr(user, field, value)


@router.get(
    "",
    response_model=IntakeStateResponse,
    summary="Current intake state (pre-fill the wizard)",
)
def read_intake(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> IntakeStateResponse:
    client = _singleton_client(db)
    requests = (
        db.execute(select(ServiceRequest).where(ServiceRequest.requested_by == user.id))
        .scalars()
        .all()
    )
    db.commit()
    return IntakeStateResponse(
        client=client,
        service_requests=list(requests),
        intake_completed_at=client.intake_completed_at,
    )


@router.patch(
    "",
    response_model=IntakeStateResponse,
    summary="Auto-save intake (partial update)",
)
def patch_intake(
    body: IntakePatchRequest,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> IntakeStateResponse:
    client = _singleton_client(db)
    if client.intake_completed_at is not None:
        # Allow edits but reset the completion stamp so the admin queue
        # can re-surface the row as updated. The spec doesn't forbid
        # re-edits and §6.4 ("never ask for the same data twice") implies
        # the client may circle back without losing data.
        client.intake_completed_at = None

    _apply_patch_to_client(client, body)
    _apply_profile_fields(
        user,
        body.model_dump(
            exclude_unset=True,
            include={"display_name", "title", "phone", "timezone"},
        ),
    )

    db.commit()
    db.refresh(client)
    db.refresh(user)

    requests = (
        db.execute(select(ServiceRequest).where(ServiceRequest.requested_by == user.id))
        .scalars()
        .all()
    )
    return IntakeStateResponse(
        client=client,
        service_requests=list(requests),
        intake_completed_at=client.intake_completed_at,
    )


@router.post(
    "/submit",
    response_model=IntakeStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize intake submission",
)
def submit_intake(
    body: IntakeSubmitRequest,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> IntakeStateResponse:
    if not body.client.legal_name or body.client.legal_name == "(pending intake)":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Organization legal name is required to submit intake.",
        )

    client = _singleton_client(db)
    _apply_patch_to_client(
        client,
        IntakePatchRequest(client=body.client),
    )
    _apply_profile_fields(
        user,
        body.model_dump(
            exclude_unset=True,
            include={"display_name", "title", "phone", "timezone"},
        ),
    )

    seen: set[str] = set()
    created_requests: list[ServiceRequest] = []
    for item in body.service_requests:
        # Don't write two requests for the same service in one submit.
        key = item.service_type.value
        if key in seen:
            continue
        seen.add(key)
        _validate_targets(item)
        sr = ServiceRequest(
            service_type=item.service_type,
            requested_by=user.id,
            notes=item.notes,
            deadline=item.deadline,
            csf_target_tier=item.csf_target_tier,
            csf_profile=item.csf_profile.value if item.csf_profile else None,
            zt_target_stage=item.zt_target_stage,
        )
        db.add(sr)
        created_requests.append(sr)

    client.intake_completed_at = utcnow()

    audit(
        db,
        action="client.intake_submitted",
        target_type="client",
        target_id=client.id,
        actor_user_id=user.id,
        details={
            "services": sorted(seen),
            "user_count": 1,
        },
    )

    # Master Spec §15 Phase 2: "Admin notification fires on intake submit."
    # Fan out to every admin so any consultant on the engagement sees it.
    # AI Prompt §6.12: the link must resolve to a working page.
    services_label = ", ".join(sorted(seen))
    notify_role(
        db,
        role=UserRole.ADMIN,
        event_type="intake.submitted",
        title="New intake submitted",
        body=(f"{client.legal_name} requested: {services_label}. " "Review in the admin queue."),
        link="/admin/queue",
    )

    db.commit()
    db.refresh(client)

    all_requests = (
        db.execute(select(ServiceRequest).where(ServiceRequest.requested_by == user.id))
        .scalars()
        .all()
    )
    return IntakeStateResponse(
        client=client,
        service_requests=list(all_requests),
        intake_completed_at=client.intake_completed_at,
    )
