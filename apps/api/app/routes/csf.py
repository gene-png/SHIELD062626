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
from app.csf.maturity import TIER_DEFINITIONS
from app.csf.scoring import compute as compute_score
from app.db.session import get_db
from app.dependencies import current_user, require_role
from app.models._common import utcnow
from app.models.csf_assessment import (
    CsfAnswer,
    CsfAssessment,
    CsfAssessmentStatus,
)
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.user import User, UserRole
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
