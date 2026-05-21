"""NIST CSF 2.0 service routes (Phase 4 stage 2).

Endpoint surface:
  POST   /csf/services
         Open a CSF assessment service. Admin-only.
  GET    /csf/catalog
         Static reference data. Any signed-in role.
  POST   /csf/services/{service_id}/assessments
         Create a draft assessment for the service. Admin-only.
  GET    /csf/services/{service_id}/assessments/latest
         Most recent assessment (admin sees draft; client sees released).
  PATCH  /csf/answers/{answer_id}
         Inline update of one subcategory answer. Admin-only.
  POST   /csf/assessments/{assessment_id}/approve
         Flip status -> approved. Admin-only.
  GET    /csf/services/{service_id}/score
         Roll-up score for the latest assessment. Admin-only.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import audit
from app.csf.catalog import (
    CATEGORIES,
    FUNCTIONS,
    SUBCATEGORIES,
    all_codes,
)
from app.csf.exporters import build_context as build_csf_context
from app.csf.exporters import render_pdf as render_csf_pdf
from app.csf.exporters import render_xlsx as render_csf_xlsx
from app.csf.gap import analyze as analyze_gaps
from app.csf.maturity import TIER_DEFINITIONS
from app.csf.scoring import compute as compute_score
from app.db.session import get_db
from app.dependencies import current_user, require_role
from app.models._common import utcnow
from app.models.artifact import Artifact, ArtifactOrigin
from app.models.client import Client
from app.models.csf_assessment import (
    CsfAnswer,
    CsfAssessment,
    CsfAssessmentStatus,
)
from app.models.deliverable import Deliverable
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.service_request import ServiceRequest
from app.models.user import User, UserRole
from app.routes.artifacts import _storage_dep
from app.schemas.csf import (
    CatalogCategory,
    CatalogFunction,
    CatalogResponse,
    CatalogSubcategory,
    CatalogTier,
    CsfAnswerPatch,
    CsfAnswerResponse,
    CsfAssessmentResponse,
    CsfScoreSummary,
    CsfServiceCreateRequest,
    CsfServiceResponse,
    FunctionScore,
    GapAnalysisResponse,
    GapItem,
)
from app.schemas.tech_debt import DeliverableResponse
from app.storage import StorageBackend
from app.tech_debt.filename import (
    SERVICE_SLUG_NIST_CSF,
    deliverable_filename,
)

router = APIRouter(prefix="/csf", tags=["csf"])

_admin_required = Depends(require_role(UserRole.ADMIN))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_answers(rows: Iterable[CsfAnswer]) -> list[CsfAnswerResponse]:
    # Stable ordering: by NIST code so the workspace tab renders predictably.
    ordered = sorted(rows, key=lambda r: r.subcategory_code)
    return [CsfAnswerResponse.model_validate(r, from_attributes=True) for r in ordered]


def _client_target_tier(db: Session, service_id: uuid.UUID) -> int | None:
    """The CSF target tier the client chose at intake, via the source request.

    Lets the admin workspace default its gap target to the client's goal
    instead of a hardcoded tier.
    """
    svc = db.get(Service, service_id)
    if svc is None or svc.source_request_id is None:
        return None
    sr = db.get(ServiceRequest, svc.source_request_id)
    return sr.csf_target_tier if sr is not None else None


def _serialize_assessment(db: Session, a: CsfAssessment) -> CsfAssessmentResponse:
    rows = (
        db.execute(select(CsfAnswer).where(CsfAnswer.assessment_id == a.id))
        .scalars()
        .all()
    )
    return CsfAssessmentResponse(
        id=a.id,
        service_id=a.service_id,
        version=a.version,
        status=a.status,
        approved_at=a.approved_at,
        approved_by=a.approved_by,
        answers=_serialize_answers(rows),
        client_target_tier=_client_target_tier(db, a.service_id),
    )


def _latest_assessment(db: Session, service_id: uuid.UUID) -> CsfAssessment | None:
    return db.execute(
        select(CsfAssessment)
        .where(CsfAssessment.service_id == service_id)
        .order_by(CsfAssessment.version.desc())
        .limit(1)
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.post(
    "/services",
    response_model=CsfServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a CSF assessment service (admin)",
)
def create_csf_service(
    body: CsfServiceCreateRequest,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CsfServiceResponse:
    if body.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service kind must be nist_csf for this endpoint.",
        )
    svc = Service(
        kind=ServiceKind.NIST_CSF,
        status=ServiceStatus.IN_PROGRESS,
        title=body.title,
        source_request_id=body.source_request_id,
        opened_by=user.id,
    )
    db.add(svc)
    db.flush()
    audit(
        db,
        action="csf.service.opened",
        target_type="service",
        target_id=svc.id,
        actor_user_id=user.id,
        details={"title": svc.title},
    )
    db.commit()
    db.refresh(svc)
    return CsfServiceResponse.model_validate(svc, from_attributes=True)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="NIST CSF 2.0 reference catalog",
)
def get_catalog(
    _user: Annotated[User, Depends(current_user)],
) -> CatalogResponse:
    functions: list[CatalogFunction] = []
    for fn in FUNCTIONS:
        categories: list[CatalogCategory] = []
        for cat in CATEGORIES:
            if cat.function != fn.code:
                continue
            subs = [
                CatalogSubcategory(
                    code=s.code,
                    function=s.function.value,
                    category=s.category,
                    name=s.name,
                    outcome=s.outcome,
                )
                for s in SUBCATEGORIES
                if s.category == cat.code
            ]
            categories.append(
                CatalogCategory(
                    code=cat.code,
                    function=cat.function.value,
                    name=cat.name,
                    purpose=cat.purpose,
                    subcategories=subs,
                )
            )
        functions.append(
            CatalogFunction(
                code=fn.code.value,
                name=fn.name,
                purpose=fn.purpose,
                categories=categories,
            )
        )
    tiers = [
        CatalogTier(tier=int(t.tier), short_label=t.short_label, description=t.description)
        for t in TIER_DEFINITIONS
    ]
    return CatalogResponse(
        functions=functions,
        tiers=tiers,
        total_subcategories=len(SUBCATEGORIES),
    )


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------


@router.post(
    "/services/{service_id}/assessments",
    response_model=CsfAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft assessment for the service (admin)",
)
def create_assessment(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CsfAssessmentResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF service not found.",
        )
    prior = _latest_assessment(db, svc.id)
    version = (prior.version + 1) if prior else 1
    assessment = CsfAssessment(
        service_id=svc.id,
        version=version,
        status=CsfAssessmentStatus.DRAFT,
    )
    db.add(assessment)
    db.flush()
    # Pre-create empty answer rows so the workspace UI gets a deterministic
    # answer grid back from the very first GET. Cheap (~106 rows).
    for sc in SUBCATEGORIES:
        db.add(
            CsfAnswer(
                assessment_id=assessment.id,
                subcategory_code=sc.code,
            )
        )
    audit(
        db,
        action="csf.assessment.created",
        target_type="csf_assessment",
        target_id=assessment.id,
        actor_user_id=user.id,
        details={"service_id": str(svc.id), "version": version},
    )
    db.commit()
    db.refresh(assessment)
    return _serialize_assessment(db, assessment)


@router.get(
    "/services/{service_id}/assessments/latest",
    response_model=CsfAssessmentResponse,
    summary="Most recent assessment for the service",
)
def latest_assessment(
    service_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CsfAssessmentResponse:
    svc = db.get(Service, service_id)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found.",
        )
    assessment = _latest_assessment(db, svc.id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    # Phase 4 keeps assessment scoreboards admin-only until the
    # deliverable is released to the client (mirrors Phase 3 stage 9).
    if user.role != UserRole.ADMIN and assessment.status != CsfAssessmentStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSF assessments are admin-only until released.",
        )
    return _serialize_assessment(db, assessment)


# ---------------------------------------------------------------------------
# Answer editing
# ---------------------------------------------------------------------------


@router.patch(
    "/answers/{answer_id}",
    response_model=CsfAnswerResponse,
    summary="Inline-update a single subcategory answer (admin)",
)
def patch_answer(
    answer_id: uuid.UUID,
    body: CsfAnswerPatch,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CsfAnswerResponse:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required.",
        )
    row = db.get(CsfAnswer, answer_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found.",
        )
    # Refuse edits to approved or released assessments.
    a = db.get(CsfAssessment, row.assessment_id)
    if a is None or a.status in (
        CsfAssessmentStatus.APPROVED,
        CsfAssessmentStatus.RELEASED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment is locked.",
        )
    # Validation: subcategory code already pinned at create-time, so we
    # only validate the tier values that arrive here.
    if "maturity_tier" in data and data["maturity_tier"] is not None:
        t = int(data["maturity_tier"])
        if not 1 <= t <= 4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="maturity_tier must be 1-4.",
            )
        row.maturity_tier = t
    elif "maturity_tier" in data:
        row.maturity_tier = None
    if "notes" in data:
        row.notes = data["notes"]
    if "evidence_artifact_id" in data:
        row.evidence_artifact_id = data["evidence_artifact_id"]
    row.answered_by = user.id
    row.answered_at = utcnow()
    audit(
        db,
        action="csf.answer.updated",
        target_type="csf_answer",
        target_id=row.id,
        actor_user_id=user.id,
        details={
            "subcategory_code": row.subcategory_code,
            "fields": sorted(data.keys()),
        },
    )
    db.commit()
    db.refresh(row)
    return CsfAnswerResponse.model_validate(row, from_attributes=True)


@router.post(
    "/assessments/{assessment_id}/approve",
    response_model=CsfAssessmentResponse,
    summary="Approve the assessment (admin)",
)
def approve_assessment(
    assessment_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CsfAssessmentResponse:
    a = db.get(CsfAssessment, assessment_id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )
    if a.status == CsfAssessmentStatus.APPROVED:
        return _serialize_assessment(db, a)
    if a.status == CsfAssessmentStatus.RELEASED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment already released.",
        )
    a.status = CsfAssessmentStatus.APPROVED
    a.approved_at = utcnow()
    a.approved_by = user.id
    audit(
        db,
        action="csf.assessment.approved",
        target_type="csf_assessment",
        target_id=a.id,
        actor_user_id=user.id,
        details={"version": a.version},
    )
    db.commit()
    db.refresh(a)
    return _serialize_assessment(db, a)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@router.get(
    "/services/{service_id}/score",
    response_model=CsfScoreSummary,
    summary="Roll-up score for the latest assessment (admin)",
)
def score_latest(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
) -> CsfScoreSummary:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF service not found.",
        )
    a = _latest_assessment(db, svc.id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    rows = db.execute(
        select(CsfAnswer).where(CsfAnswer.assessment_id == a.id)
    ).scalars().all()
    answers: dict[str, int | None] = {r.subcategory_code: r.maturity_tier for r in rows}
    # Defensive: ignore unknown codes.
    valid = all_codes()
    answers = {k: v for k, v in answers.items() if k in valid}
    score = compute_score(answers)
    return CsfScoreSummary(
        assessment_id=a.id,
        version=a.version,
        total_subcategories=score.total_subcategories,
        answered_subcategories=score.answered_subcategories,
        coverage_pct=score.coverage_pct,
        average_tier=score.average_tier,
        overall_maturity_label=score.overall_maturity_label,
        by_function=[
            FunctionScore(
                function=fs.function.value,
                function_name=fs.function_name,
                subcategory_count=fs.subcategory_count,
                answered_count=fs.answered_count,
                average_tier=fs.average_tier,
                coverage_pct=fs.coverage_pct,
                weakest_subcategory_codes=list(fs.weakest_subcategory_codes),
            )
            for fs in score.by_function
        ],
    )


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------


@router.get(
    "/services/{service_id}/gap-analysis",
    response_model=GapAnalysisResponse,
    summary="Prioritized remediation gaps for the latest assessment (admin)",
)
def gap_analysis(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    target_tier: int = 3,
    top_n: int = 20,
) -> GapAnalysisResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF service not found.",
        )
    a = _latest_assessment(db, svc.id)
    if a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    rows = (
        db.execute(select(CsfAnswer).where(CsfAnswer.assessment_id == a.id))
        .scalars()
        .all()
    )
    valid = all_codes()
    answers: dict[str, int | None] = {
        r.subcategory_code: r.maturity_tier for r in rows if r.subcategory_code in valid
    }
    notes: dict[str, str | None] = {
        r.subcategory_code: r.notes for r in rows if r.subcategory_code in valid
    }
    analysis = analyze_gaps(
        answers, notes=notes, target_tier=target_tier, top_n=top_n
    )
    return GapAnalysisResponse(
        assessment_id=a.id,
        version=a.version,
        target_tier=analysis.target_tier,
        target_label=analysis.target_label,
        total_gap_count=analysis.total_gap_count,
        unscored_count=len(analysis.unscored_codes),
        gap_count_by_function=analysis.gap_count_by_function,
        gaps=[
            GapItem(
                code=g.code,
                function=g.function.value,
                function_name=g.function_name,
                category=g.category,
                name=g.name,
                outcome=g.outcome,
                current_tier=g.current_tier,
                target_tier=g.target_tier,
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
        stage="csf.deliverable",
        uploaded_by=user.id,
    )
    db.add(art)
    db.flush()
    return art


@router.post(
    "/services/{service_id}/deliverables/finalize",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Render PDF + XLSX deliverable from the latest approved CSF assessment (admin)",
)
def finalize_csf_deliverable(
    service_id: uuid.UUID,
    user: Annotated[User, _admin_required],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(_storage_dep)],
) -> DeliverableResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF service not found.",
        )
    assessment = _latest_assessment(db, svc.id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet.",
        )
    if assessment.status not in (
        CsfAssessmentStatus.APPROVED,
        CsfAssessmentStatus.RELEASED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment must be approved before finalizing the deliverable.",
        )
    answers = (
        db.execute(select(CsfAnswer).where(CsfAnswer.assessment_id == assessment.id))
        .scalars()
        .all()
    )
    valid = all_codes()
    tier_map: dict[str, int | None] = {
        r.subcategory_code: r.maturity_tier
        for r in answers
        if r.subcategory_code in valid
    }
    notes_map: dict[str, str | None] = {
        r.subcategory_code: r.notes for r in answers if r.subcategory_code in valid
    }
    score = compute_score(tier_map)
    gap = analyze_gaps(tier_map, notes=notes_map)

    client = db.execute(select(Client).limit(1)).scalar_one_or_none()
    client_name = client.legal_name if client is not None else None
    if client_name == "(pending intake)":
        client_name = None

    # Filename version: same-day re-finalize -> v2, v3, ...
    today = utcnow().date()
    existing_count = db.execute(
        select(Deliverable).where(Deliverable.service_id == svc.id)
    ).all()
    next_version = len(existing_count) + 1

    pdf_name = deliverable_filename(
        company=client_name,
        service_slug=SERVICE_SLUG_NIST_CSF,
        extension="pdf",
        day=today,
        version=next_version,
    )
    xlsx_name = deliverable_filename(
        company=client_name,
        service_slug=SERVICE_SLUG_NIST_CSF,
        extension="xlsx",
        day=today,
        version=next_version,
    )

    ctx = build_csf_context(
        client_legal_name=client_name,
        service_title=svc.title,
        assessment=assessment,
        answers=answers,
        score=score,
        gap=gap,
    )
    pdf_bytes = render_csf_pdf(ctx)
    xlsx_bytes = render_csf_xlsx(ctx)

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
        f"Overall maturity: {score.overall_maturity_label}. "
        f"{score.answered_subcategories}/{score.total_subcategories} subcategories scored; "
        f"{gap.total_gap_count} gap(s) at target T{gap.target_tier}."
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
        action="csf.deliverable.finalized",
        target_type="deliverable",
        target_id=deliv.id,
        actor_user_id=user.id,
        details={
            "service_id": str(svc.id),
            "assessment_id": str(assessment.id),
            "assessment_version": assessment.version,
            "version": next_version,
            "overall_maturity_label": score.overall_maturity_label,
            "average_tier": score.average_tier,
            "coverage_pct": score.coverage_pct,
            "gap_count": gap.total_gap_count,
        },
    )
    db.commit()
    db.refresh(deliv)
    return _serialize_deliverable(db, deliv)


@router.post(
    "/deliverables/{deliverable_id}/release",
    response_model=DeliverableResponse,
    summary="Release a finalized CSF deliverable to the client (admin)",
)
def release_csf_deliverable(
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
    # Mirror the assessment status so the latest-assessment client
    # gate (admin-only until released) unlocks.
    a = _latest_assessment(db, deliv.service_id)
    if a is not None and a.status != CsfAssessmentStatus.RELEASED:
        a.status = CsfAssessmentStatus.RELEASED

    audit(
        db,
        action="csf.deliverable.released",
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
    summary="Most recent CSF deliverable for a service",
)
def latest_csf_deliverable(
    service_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DeliverableResponse:
    svc = db.get(Service, service_id)
    if svc is None or svc.kind != ServiceKind.NIST_CSF:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSF service not found.",
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
