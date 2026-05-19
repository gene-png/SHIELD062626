"""Tech Debt service routes (Master Spec §15 Phase 3).

This stage (Phase 3 stage 4) ships the spine:
  - POST /tech-debt/services         (open a service workspace; admin-only)
  - POST /tech-debt/services/{id}/capability-lists/extract
        (run the AI extraction; produces a new versioned CapabilityList)
  - GET  /tech-debt/services/{id}/capability-lists/latest

The editable extraction table (PATCH per item, approve list) lands in
stage 5; overlap analysis in stage 6; consolidation plan in stage 7;
deliverable render in stage 8; client release in stage 9.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm import LLMClient
from app.audit import audit
from app.db.session import get_db
from app.dependencies import current_user, require_role
from app.models.artifact import Artifact
from app.models.capability import CapabilityItem, CapabilityList
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.user import User, UserRole
from app.routes.artifacts import _storage_dep
from app.models._common import utcnow
from app.models.capability import CapabilityListStatus
from app.schemas.tech_debt import (
    CapabilityItemPatch,
    CapabilityItemResponse,
    CapabilityListResponse,
    ExtractRequest,
    ServiceCreateRequest,
    ServiceResponse,
)
from app.storage import StorageBackend
from app.tech_debt.extract import (
    client_org_name_for_deployment,
    extract_capabilities,
    name_hints_for_deployment,
)
from app.tech_debt.parsers import SUPPORTED_MIME, UnsupportedInventoryFormat

router = APIRouter(prefix="/tech-debt", tags=["tech-debt"])

_admin_required = Depends(require_role(UserRole.ADMIN))


# Module-level slot for tests + production. Tests inject a FixtureProvider-
# backed client via FastAPI dependency overrides; production gets the
# settings-built client lazily.
def _llm_dep() -> LLMClient:
    return LLMClient.from_settings()


@router.post(
    "/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a service workspace (admin)",
)
def create_service(
    body: ServiceCreateRequest,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ServiceResponse:
    svc = Service(
        kind=body.kind,
        status=ServiceStatus.IN_PROGRESS,
        title=body.title,
        source_request_id=body.source_request_id,
        opened_by=user.id,
    )
    db.add(svc)
    db.flush()
    audit(
        db,
        action="service.opened",
        target_type="service",
        target_id=svc.id,
        actor_user_id=user.id,
        details={
            "kind": body.kind.value,
            "source_request_id": str(body.source_request_id) if body.source_request_id else None,
        },
    )
    db.commit()
    db.refresh(svc)
    return ServiceResponse.model_validate(svc, from_attributes=True)


def _latest_list_or_none(db: Session, service_id: uuid.UUID) -> CapabilityList | None:
    return db.execute(
        select(CapabilityList)
        .where(CapabilityList.service_id == service_id)
        .order_by(CapabilityList.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def _serialize_list_with_items(db: Session, cap_list: CapabilityList) -> CapabilityListResponse:
    items = (
        db.execute(select(CapabilityItem).where(CapabilityItem.capability_list_id == cap_list.id))
        .scalars()
        .all()
    )
    return CapabilityListResponse(
        id=cap_list.id,
        service_id=cap_list.service_id,
        version=cap_list.version,
        status=cap_list.status,
        items=[CapabilityItemResponse.model_validate(i, from_attributes=True) for i in items],
        approved_at=cap_list.approved_at,
        approved_by=cap_list.approved_by,
    )


@router.post(
    "/services/{service_id}/capability-lists/extract",
    response_model=CapabilityListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract capability list from an inventory artifact (admin)",
)
def extract_capability_list(
    service_id: uuid.UUID,
    body: ExtractRequest,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(_storage_dep)],
    llm: Annotated[LLMClient, Depends(_llm_dep)],
) -> CapabilityListResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.TECH_DEBT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tech-Debt service not found.",
        )
    artifact = db.get(Artifact, body.artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source artifact not found.",
        )
    if artifact.mime_type not in SUPPORTED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(f"Inventory MIME {artifact.mime_type!r} is not supported. " "Use CSV or XLSX."),
        )

    try:
        result = extract_capabilities(
            db=db,
            storage=storage,
            artifact=artifact,
            requested_by=user,
            service_id=svc.id,
            client_org_name=client_org_name_for_deployment(db),
            name_hints=name_hints_for_deployment(db),
            llm=llm,
        )
    except UnsupportedInventoryFormat as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        # LLM returned unparseable JSON. The llm_calls row is already
        # written; surface a 502 so the admin sees this is upstream, not
        # client error.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI extraction failed to parse: {exc}",
        ) from exc

    # Determine next version.
    last = _latest_list_or_none(db, svc.id)
    next_version = (last.version + 1) if last else 1
    cap_list = CapabilityList(service_id=svc.id, version=next_version)
    db.add(cap_list)
    db.flush()

    for item in result.items:
        db.add(
            CapabilityItem(
                capability_list_id=cap_list.id,
                name=item.name,
                vendor=item.vendor,
                category=item.category,
                function=item.function,
                annual_cost_usd=item.annual_cost_usd,
                license_count=item.license_count,
                notes=item.notes,
                confidence_pct=item.confidence_pct,
                source_artifact_id=artifact.id,
            )
        )

    audit(
        db,
        action="capability_list.extracted",
        target_type="capability_list",
        target_id=cap_list.id,
        actor_user_id=user.id,
        details={
            "service_id": str(svc.id),
            "version": next_version,
            "artifact_id": str(artifact.id),
            "item_count": len(result.items),
            "llm_call_id": str(result.llm_call.id),
        },
    )
    db.commit()
    db.refresh(cap_list)
    return _serialize_list_with_items(db, cap_list)


@router.get(
    "/services/{service_id}/capability-lists/latest",
    response_model=CapabilityListResponse,
    summary="Most recent capability list for a service",
)
def latest_capability_list(
    service_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CapabilityListResponse:
    svc = db.get(Service, service_id)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )
    cap_list = _latest_list_or_none(db, svc.id)
    if cap_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No capability list yet. Run extraction first.",
        )
    # Phase 3 admin-only for now; client view of the released deliverable
    # comes in stage 9 via /deliverables/.
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Capability lists are admin-only until release.",
        )
    return _serialize_list_with_items(db, cap_list)


@router.patch(
    "/capability-items/{item_id}",
    response_model=CapabilityItemResponse,
    summary="Inline-edit a single capability item (admin)",
)
def patch_capability_item(
    item_id: uuid.UUID,
    body: CapabilityItemPatch,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CapabilityItemResponse:
    item = db.get(CapabilityItem, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capability item not found.",
        )
    # Refuse edits to items that belong to a released list.
    cap_list = db.get(CapabilityList, item.capability_list_id)
    if cap_list is not None and cap_list.status == CapabilityListStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This capability list has been released and is locked.",
        )

    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patch body is empty.",
        )
    for field, value in data.items():
        setattr(item, field, value)
    # Human edit -> no longer an AI guess.
    item.confidence_pct = None

    audit(
        db,
        action="capability_item.edited",
        target_type="capability_item",
        target_id=item.id,
        actor_user_id=user.id,
        details={
            "fields": sorted(data.keys()),
            "capability_list_id": str(item.capability_list_id),
        },
    )
    db.commit()
    db.refresh(item)
    return CapabilityItemResponse.model_validate(item, from_attributes=True)


@router.post(
    "/capability-lists/{list_id}/approve",
    response_model=CapabilityListResponse,
    summary="Approve a capability list (admin)",
)
def approve_capability_list(
    list_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CapabilityListResponse:
    cap_list = db.get(CapabilityList, list_id)
    if cap_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capability list not found.",
        )
    if cap_list.status == CapabilityListStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This capability list has been released and is locked.",
        )
    cap_list.status = CapabilityListStatus.APPROVED
    cap_list.approved_at = utcnow()
    cap_list.approved_by = user.id
    audit(
        db,
        action="capability_list.approved",
        target_type="capability_list",
        target_id=cap_list.id,
        actor_user_id=user.id,
        details={"service_id": str(cap_list.service_id), "version": cap_list.version},
    )
    db.commit()
    db.refresh(cap_list)
    return _serialize_list_with_items(db, cap_list)
