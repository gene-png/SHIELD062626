"""Zero Trust assessment routes (Phase 5 stage 2).

Mirrors the CSF route layout but parameterized by framework. The
framework is locked at service-create time via Service.kind:

  kind=zero_trust_cisa -> ZtFramework.CISA_ZTMM_2_0
  kind=zero_trust_dod  -> ZtFramework.DOD_ZTRA

Endpoint surface:
  POST   /zt/services
  GET    /zt/catalog?framework=cisa_ztmm_2_0|dod_ztra
  POST   /zt/services/{service_id}/assessments
  GET    /zt/services/{service_id}/assessments/latest
  PATCH  /zt/answers/{answer_id}
  POST   /zt/assessments/{assessment_id}/approve
  GET    /zt/services/{service_id}/score
  GET    /zt/services/{service_id}/gap-analysis
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import audit
from app.db.session import get_db
from app.dependencies import current_user, require_role
from app.models._common import utcnow
from app.models.artifact import Artifact, ArtifactOrigin
from app.models.client import Client
from app.models.deliverable import Deliverable
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.service_request import ServiceRequest
from app.models.user import User, UserRole
from app.models.zt_assessment import (
    ZtAnswer,
    ZtAssessment,
    ZtAssessmentStatus,
    ZtFramework,
)
from app.routes.artifacts import _storage_dep
from app.schemas.tech_debt import DeliverableResponse
from app.schemas.zt import (
    CatalogCapability,
    CatalogPillar,
    CatalogResponse,
    CatalogStage,
    GapAnalysisResponse,
    GapItem,
    PillarScore,
    ZtAnswerPatch,
    ZtAnswerResponse,
    ZtAssessmentResponse,
    ZtScoreSummary,
    ZtServiceCreateRequest,
    ZtServiceResponse,
)
from app.storage import StorageBackend
from app.tech_debt.filename import (
    SERVICE_SLUG_ZT_CISA,
    SERVICE_SLUG_ZT_DOD,
    deliverable_filename,
)
from app.zt.catalog import (
    all_codes,
    capabilities,
    pillars,
)
from app.zt.exporters import build_context as build_zt_context
from app.zt.exporters import render_pdf as render_zt_pdf
from app.zt.exporters import render_xlsx as render_zt_xlsx
from app.zt.maturity import STAGE_DEFINITIONS, ZtFrameworkCode
from app.zt.scoring import analyze_gaps
from app.zt.scoring import compute as compute_score

router = APIRouter(prefix="/zt", tags=["zt"])

_admin_required = Depends(require_role(UserRole.ADMIN))


# ---------------------------------------------------------------------------
# Framework <-> ServiceKind mapping
# ---------------------------------------------------------------------------

_SERVICE_KIND_TO_FRAMEWORK: dict[ServiceKind, ZtFramework] = {
    ServiceKind.ZERO_TRUST_CISA: ZtFramework.CISA_ZTMM_2_0,
    ServiceKind.ZERO_TRUST_DOD: ZtFramework.DOD_ZTRA,
}


def _framework_for_kind(kind: ServiceKind) -> ZtFramework:
    try:
        return _SERVICE_KIND_TO_FRAMEWORK[kind]
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service kind must be zero_trust_cisa or zero_trust_dod.",
        ) from exc


def _to_catalog_framework(fw: ZtFramework) -> ZtFrameworkCode:
    return (
        ZtFrameworkCode.CISA_ZTMM_2_0
        if fw == ZtFramework.CISA_ZTMM_2_0
        else ZtFrameworkCode.DOD_ZTRA
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_answers(rows: Iterable[ZtAnswer]) -> list[ZtAnswerResponse]:
    ordered = sorted(rows, key=lambda r: r.capability_code)
    return [ZtAnswerResponse.model_validate(r, from_attributes=True) for r in ordered]


def _client_target_stage(db: Session, service_id: uuid.UUID) -> int | None:
    """The ZT target stage the client chose at intake, via the source request.

    Lets the admin workspace default its gap target to the client's goal
    instead of a hardcoded stage.
    """
    svc = db.get(Service, service_id)
    if svc is None or svc.source_request_id is None:
        return None
    sr = db.get(ServiceRequest, svc.source_request_id)
    return sr.zt_target_stage if sr is not None else None


def _serialize_assessment(db: Session, a: ZtAssessment) -> ZtAssessmentResponse:
    rows = (
        db.execute(select(ZtAnswer).where(ZtAnswer.assessment_id == a.id))
        .scalars()
        .all()
    )
    return ZtAssessmentResponse(
        id=a.id,
        service_id=a.service_id,
        framework=a.framework,
        version=a.version,
        status=a.status,
        approved_at=a.approved_at,
        approved_by=a.approved_by,
        answers=_serialize_answers(rows),
        client_target_stage=_client_target_stage(db, a.service_id),
    )


def _latest_assessment(db: Session, service_id: uuid.UUID) -> ZtAssessment | None:
    return db.execute(
        select(ZtAssessment)
        .where(ZtAssessment.service_id == service_id)
        .order_by(ZtAssessment.version.desc())
        .limit(1)
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.post(
    "/services",
    response_model=ZtServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a Zero Trust assessment service (admin)",
)
def create_zt_service(
    body: ZtServiceCreateRequest,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ZtServiceResponse:
    framework = _framework_for_kind(body.kind)
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
        action="zt.service.opened",
        target_type="service",
        target_id=svc.id,
        actor_user_id=user.id,
        details={"title": svc.title, "framework": framework.value},
    )
    db.commit()
    db.refresh(svc)
    return ZtServiceResponse.model_validate(svc, from_attributes=True)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Zero Trust reference catalog",
)
def get_catalog(
    _user: Annotated[User, Depends(current_user)],
    framework: Annotated[
        ZtFramework,
        Query(description="cisa_ztmm_2_0 or dod_ztra"),
    ] = ZtFramework.CISA_ZTMM_2_0,
) -> CatalogResponse:
    cat_fw = _to_catalog_framework(framework)
    pillar_rows: list[CatalogPillar] = []
    for p in pillars(cat_fw):
        caps = [
            CatalogCapability(
                code=c.code,
                pillar_code=c.pillar_code,
                name=c.name,
                outcome=c.outcome,
            )
            for c in capabilities(cat_fw)
            if c.pillar_code == p.code
        ]
        pillar_rows.append(
            CatalogPillar(
                code=p.code,
                name=p.name,
                purpose=p.purpose,
                capabilities=caps,
            )
        )
    stages = [
        CatalogStage(
            stage=int(d.stage),
            label=(d.cisa_label if cat_fw == ZtFrameworkCode.CISA_ZTMM_2_0 else d.dod_label),
            description=d.description,
        )
        for d in STAGE_DEFINITIONS
    ]
    total = sum(len(p.capabilities) for p in pillar_rows)
    return CatalogResponse(
        framework=framework,
        pillars=pillar_rows,
        stages=stages,
        total_capabilities=total,
    )


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------


@router.post(
    "/services/{service_id}/assessments",
    response_model=ZtAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft Zero Trust assessment (admin)",
)
def create_assessment(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ZtAssessmentResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind not in _SERVICE_KIND_TO_FRAMEWORK:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zero Trust service not found.",
        )
    framework = _framework_for_kind(svc.kind)
    cat_fw = _to_catalog_framework(framework)

    prior = _latest_assessment(db, svc.id)
    version = (prior.version + 1) if prior else 1
    assessment = ZtAssessment(
        service_id=svc.id,
        framework=framework,
        version=version,
        status=ZtAssessmentStatus.DRAFT,
    )
    db.add(assessment)
    db.flush()
    for cap in capabilities(cat_fw):
        db.add(
            ZtAnswer(
                assessment_id=assessment.id,
                capability_code=cap.code,
            )
        )
    audit(
        db,
        action="zt.assessment.created",
        target_type="zt_assessment",
        target_id=assessment.id,
        actor_user_id=user.id,
        details={
            "service_id": str(svc.id),
            "version": version,
            "framework": framework.value,
        },
    )
    db.commit()
    db.refresh(assessment)
    return _serialize_assessment(db, assessment)


@router.get(
    "/services/{service_id}/assessments/latest",
    response_model=ZtAssessmentResponse,
    summary="Most recent Zero Trust assessment",
)
def latest_assessment(
    service_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ZtAssessmentResponse:
    svc = db.get(Service, service_id)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )
    a = _latest_assessment(db, svc.id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    if user.role != UserRole.ADMIN and a.status != ZtAssessmentStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ZT assessments are admin-only until released.",
        )
    return _serialize_assessment(db, a)


# ---------------------------------------------------------------------------
# Answer editing
# ---------------------------------------------------------------------------


@router.patch(
    "/answers/{answer_id}",
    response_model=ZtAnswerResponse,
    summary="Inline-update a single capability answer (admin)",
)
def patch_answer(
    answer_id: uuid.UUID,
    body: ZtAnswerPatch,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ZtAnswerResponse:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required.",
        )
    row = db.get(ZtAnswer, answer_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found.",
        )
    a = db.get(ZtAssessment, row.assessment_id)
    if a is None or a.status in (
        ZtAssessmentStatus.APPROVED,
        ZtAssessmentStatus.RELEASED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment is locked.",
        )
    if "maturity_stage" in data and data["maturity_stage"] is not None:
        s = int(data["maturity_stage"])
        if not 1 <= s <= 4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="maturity_stage must be 1-4.",
            )
        row.maturity_stage = s
    elif "maturity_stage" in data:
        row.maturity_stage = None
    if "notes" in data:
        row.notes = data["notes"]
    if "evidence_artifact_id" in data:
        row.evidence_artifact_id = data["evidence_artifact_id"]
    row.answered_by = user.id
    row.answered_at = utcnow()
    audit(
        db,
        action="zt.answer.updated",
        target_type="zt_answer",
        target_id=row.id,
        actor_user_id=user.id,
        details={
            "capability_code": row.capability_code,
            "fields": sorted(data.keys()),
        },
    )
    db.commit()
    db.refresh(row)
    return ZtAnswerResponse.model_validate(row, from_attributes=True)


@router.post(
    "/assessments/{assessment_id}/approve",
    response_model=ZtAssessmentResponse,
    summary="Approve the Zero Trust assessment (admin)",
)
def approve_assessment(
    assessment_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ZtAssessmentResponse:
    a = db.get(ZtAssessment, assessment_id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )
    if a.status == ZtAssessmentStatus.APPROVED:
        return _serialize_assessment(db, a)
    if a.status == ZtAssessmentStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment already released.",
        )
    a.status = ZtAssessmentStatus.APPROVED
    a.approved_at = utcnow()
    a.approved_by = user.id
    audit(
        db,
        action="zt.assessment.approved",
        target_type="zt_assessment",
        target_id=a.id,
        actor_user_id=user.id,
        details={"version": a.version, "framework": a.framework.value},
    )
    db.commit()
    db.refresh(a)
    return _serialize_assessment(db, a)


# ---------------------------------------------------------------------------
# Scoring + gap
# ---------------------------------------------------------------------------


@router.get(
    "/services/{service_id}/score",
    response_model=ZtScoreSummary,
    summary="Roll-up score for the latest Zero Trust assessment (admin)",
)
def score_latest(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> ZtScoreSummary:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind not in _SERVICE_KIND_TO_FRAMEWORK:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zero Trust service not found.",
        )
    a = _latest_assessment(db, svc.id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    cat_fw = _to_catalog_framework(a.framework)
    valid = all_codes(cat_fw)
    rows = (
        db.execute(select(ZtAnswer).where(ZtAnswer.assessment_id == a.id))
        .scalars()
        .all()
    )
    answers: dict[str, int | None] = {
        r.capability_code: r.maturity_stage
        for r in rows
        if r.capability_code in valid
    }
    score = compute_score(cat_fw, answers)
    return ZtScoreSummary(
        assessment_id=a.id,
        version=a.version,
        framework=a.framework,
        total_capabilities=score.total_capabilities,
        answered_capabilities=score.answered_capabilities,
        coverage_pct=score.coverage_pct,
        average_stage=score.average_stage,
        overall_stage_label=score.overall_stage_label,
        by_pillar=[
            PillarScore(
                pillar_code=ps.pillar_code,
                pillar_name=ps.pillar_name,
                capability_count=ps.capability_count,
                answered_count=ps.answered_count,
                average_stage=ps.average_stage,
                coverage_pct=ps.coverage_pct,
                weakest_capability_codes=list(ps.weakest_capability_codes),
            )
            for ps in score.by_pillar
        ],
    )


@router.get(
    "/services/{service_id}/gap-analysis",
    response_model=GapAnalysisResponse,
    summary="Prioritized remediation gaps for the latest assessment (admin)",
)
def gap_analysis(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    target_stage: int = 3,
    top_n: int = 20,
) -> GapAnalysisResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind not in _SERVICE_KIND_TO_FRAMEWORK:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zero Trust service not found.",
        )
    a = _latest_assessment(db, svc.id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    cat_fw = _to_catalog_framework(a.framework)
    valid = all_codes(cat_fw)
    rows = (
        db.execute(select(ZtAnswer).where(ZtAnswer.assessment_id == a.id))
        .scalars()
        .all()
    )
    answers: dict[str, int | None] = {
        r.capability_code: r.maturity_stage
        for r in rows
        if r.capability_code in valid
    }
    notes: dict[str, str | None] = {
        r.capability_code: r.notes for r in rows if r.capability_code in valid
    }
    analysis = analyze_gaps(
        cat_fw, answers, notes=notes, target_stage=target_stage, top_n=top_n
    )
    return GapAnalysisResponse(
        assessment_id=a.id,
        version=a.version,
        framework=a.framework,
        target_stage=analysis.target_stage,
        target_label=analysis.target_label,
        total_gap_count=analysis.total_gap_count,
        unscored_count=len(analysis.unscored_codes),
        gap_count_by_pillar=analysis.gap_count_by_pillar,
        gaps=[
            GapItem(
                code=g.code,
                pillar_code=g.pillar_code,
                pillar_name=g.pillar_name,
                name=g.name,
                outcome=g.outcome,
                current_stage=g.current_stage,
                target_stage=g.target_stage,
                gap_size=g.gap_size,
                priority_score=g.priority_score,
                notes=g.notes,
            )
            for g in analysis.gaps
        ],
    )


# ---------------------------------------------------------------------------
# Deliverables
# ---------------------------------------------------------------------------


_SERVICE_SLUG_BY_FRAMEWORK: dict[ZtFramework, str] = {
    ZtFramework.CISA_ZTMM_2_0: SERVICE_SLUG_ZT_CISA,
    ZtFramework.DOD_ZTRA: SERVICE_SLUG_ZT_DOD,
}


def _serialize_deliverable(db: Session, deliv: Deliverable) -> DeliverableResponse:
    pdf_title = None
    xlsx_title = None
    if deliv.pdf_artifact_id:
        a = db.get(Artifact, deliv.pdf_artifact_id)
        pdf_title = a.title if a else None
    if deliv.xlsx_artifact_id:
        a = db.get(Artifact, deliv.xlsx_artifact_id)
        xlsx_title = a.title if a else None
    return DeliverableResponse(
        id=deliv.id,
        service_id=deliv.service_id,
        title=deliv.title,
        summary=deliv.summary,
        version=deliv.version,
        pdf_artifact_id=deliv.pdf_artifact_id,
        xlsx_artifact_id=deliv.xlsx_artifact_id,
        pdf_filename=pdf_title,
        xlsx_filename=xlsx_title,
        finalized_at=deliv.finalized_at,
        finalized_by=deliv.finalized_by,
        released_to_client_at=deliv.released_to_client_at,
        superseded_by=deliv.superseded_by,
    )


def _write_artifact(
    db: Session,
    *,
    storage: StorageBackend,
    user: User,
    filename: str,
    mime_type: str,
    data: bytes,
) -> Artifact:
    from hashlib import sha256

    key = f"deliverable/{user.id}/{uuid.uuid4()}/{filename}"
    storage.put(key, data, content_type=mime_type)
    art = Artifact(
        title=filename,
        file_storage_key=key,
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=sha256(data).hexdigest(),
        origin=ArtifactOrigin.CONSULTANT_APPROVED,
        stage="zt.deliverable",
        uploaded_by=user.id,
    )
    db.add(art)
    db.flush()
    return art


@router.post(
    "/services/{service_id}/deliverables/finalize",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Render PDF + XLSX deliverable from the latest approved ZT assessment (admin)",
)
def finalize_zt_deliverable(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(_storage_dep)],
) -> DeliverableResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind not in _SERVICE_KIND_TO_FRAMEWORK:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zero Trust service not found.",
        )
    assessment = _latest_assessment(db, svc.id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    if assessment.status not in (
        ZtAssessmentStatus.APPROVED,
        ZtAssessmentStatus.RELEASED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment must be approved before finalizing the deliverable.",
        )
    cat_fw = _to_catalog_framework(assessment.framework)
    valid = all_codes(cat_fw)
    answers = (
        db.execute(select(ZtAnswer).where(ZtAnswer.assessment_id == assessment.id))
        .scalars()
        .all()
    )
    stage_map: dict[str, int | None] = {
        r.capability_code: r.maturity_stage
        for r in answers
        if r.capability_code in valid
    }
    notes_map: dict[str, str | None] = {
        r.capability_code: r.notes for r in answers if r.capability_code in valid
    }
    score = compute_score(cat_fw, stage_map)
    gap = analyze_gaps(cat_fw, stage_map, notes=notes_map)

    client = db.execute(select(Client).limit(1)).scalar_one_or_none()
    client_name = client.legal_name if client is not None else None
    if client_name == "(pending intake)":
        client_name = None

    today = utcnow().date()
    existing = db.execute(
        select(Deliverable).where(Deliverable.service_id == svc.id)
    ).all()
    next_version = len(existing) + 1

    service_slug = _SERVICE_SLUG_BY_FRAMEWORK[assessment.framework]
    pdf_name = deliverable_filename(
        company=client_name,
        service_slug=service_slug,
        extension="pdf",
        day=today,
        version=next_version,
    )
    xlsx_name = deliverable_filename(
        company=client_name,
        service_slug=service_slug,
        extension="xlsx",
        day=today,
        version=next_version,
    )

    ctx = build_zt_context(
        client_legal_name=client_name,
        service_title=svc.title,
        framework=cat_fw,
        assessment=assessment,
        answers=answers,
        score=score,
        gap=gap,
    )
    pdf_bytes = render_zt_pdf(ctx)
    xlsx_bytes = render_zt_xlsx(ctx)

    pdf_artifact = _write_artifact(
        db,
        storage=storage,
        user=user,
        filename=pdf_name,
        mime_type="application/pdf",
        data=pdf_bytes,
    )
    xlsx_artifact = _write_artifact(
        db,
        storage=storage,
        user=user,
        filename=xlsx_name,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        data=xlsx_bytes,
    )

    summary_line = (
        f"Overall stage: {score.overall_stage_label}. "
        f"{score.answered_capabilities}/{score.total_capabilities} capabilities scored; "
        f"{gap.total_gap_count} gap(s) at target S{gap.target_stage}."
    )

    deliv = Deliverable(
        service_id=svc.id,
        title=f"{svc.title} v{next_version}",
        summary=summary_line,
        version=next_version,
        pdf_artifact_id=pdf_artifact.id,
        xlsx_artifact_id=xlsx_artifact.id,
        finalized_at=utcnow(),
        finalized_by=user.id,
    )
    db.add(deliv)
    db.flush()

    audit(
        db,
        action="zt.deliverable.finalized",
        target_type="deliverable",
        target_id=deliv.id,
        actor_user_id=user.id,
        details={
            "service_id": str(svc.id),
            "assessment_id": str(assessment.id),
            "framework": assessment.framework.value,
            "assessment_version": assessment.version,
            "version": next_version,
            "overall_stage_label": score.overall_stage_label,
            "average_stage": score.average_stage,
            "gap_count": gap.total_gap_count,
        },
    )
    db.commit()
    db.refresh(deliv)
    return _serialize_deliverable(db, deliv)


@router.post(
    "/deliverables/{deliverable_id}/release",
    response_model=DeliverableResponse,
    summary="Release a finalized ZT deliverable to the client (admin)",
)
def release_zt_deliverable(
    deliverable_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse:
    deliv = db.get(Deliverable, deliverable_id)
    if deliv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deliverable not found.",
        )
    if deliv.finalized_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deliverable must be finalized before release.",
        )
    if deliv.released_to_client_at is not None:
        return _serialize_deliverable(db, deliv)
    deliv.released_to_client_at = utcnow()
    earlier = (
        db.execute(
            select(Deliverable).where(
                Deliverable.service_id == deliv.service_id,
                Deliverable.id != deliv.id,
                Deliverable.superseded_by.is_(None),
            )
        )
        .scalars()
        .all()
    )
    for prev in earlier:
        prev.superseded_by = deliv.id
    a = _latest_assessment(db, deliv.service_id)
    if a is not None and a.status != ZtAssessmentStatus.RELEASED:
        a.status = ZtAssessmentStatus.RELEASED
    audit(
        db,
        action="zt.deliverable.released",
        target_type="deliverable",
        target_id=deliv.id,
        actor_user_id=user.id,
        details={
            "service_id": str(deliv.service_id),
            "version": deliv.version,
            "superseded": [str(p.id) for p in earlier],
        },
    )
    db.commit()
    db.refresh(deliv)
    return _serialize_deliverable(db, deliv)


@router.get(
    "/services/{service_id}/deliverables/latest",
    response_model=DeliverableResponse,
    summary="Most recent ZT deliverable for a service",
)
def latest_zt_deliverable(
    service_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind not in _SERVICE_KIND_TO_FRAMEWORK:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zero Trust service not found.",
        )
    deliv = db.execute(
        select(Deliverable)
        .where(Deliverable.service_id == svc.id)
        .order_by(Deliverable.version.desc())
        .limit(1)
    ).scalar_one_or_none()
    if deliv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deliverable yet. Finalize one first.",
        )
    if user.role != UserRole.ADMIN and deliv.released_to_client_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No released deliverable yet.",
        )
    return _serialize_deliverable(db, deliv)
