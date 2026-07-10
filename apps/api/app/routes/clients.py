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

from app.attack.analytics import compute as attack_compute
from app.csf.gap import analyze as csf_analyze_gaps
from app.db.session import get_db
from app.dependencies import current_client, current_user
from app.logging import get_logger
from app.models.artifact import Artifact
from app.models.attack_assessment import (
    AttackAssessment,
    AttackAssessmentStatus,
    AttackCoverage,
)
from app.models.capability import (
    CapabilityDisposition,
    CapabilityItem,
    CapabilityList,
    CapabilityListStatus,
)
from app.models.client import Client
from app.models.csf_assessment import CsfAnswer, CsfAssessment, CsfAssessmentStatus
from app.models.deliverable import Deliverable
from app.models.service import Service, ServiceKind
from app.models.user import User
from app.models.zt_assessment import (
    ZtAnswer,
    ZtAssessment,
    ZtAssessmentStatus,
    ZtFramework,
)
from app.schemas.clients import (
    ClientDeliverableListResponse,
    ClientDeliverableResponse,
    ValueSummaryResponse,
)
from app.zt.maturity import ZtFrameworkCode
from app.zt.scoring import analyze_gaps as zt_analyze_gaps

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


# ---------------------------------------------------------------------------
# Cross-service value loop (Master Spec §2.5)
#
# "AI suggests, code computes." Every number below is recomputed by a pure
# deterministic engine over the frozen post-release answer rows — never an LLM
# call. A service only feeds the client-visible summary once it has a RELEASED
# deliverable (§12): a service without one contributes null (the card renders
# "pending"), so a pre-release number can never leak.
# ---------------------------------------------------------------------------


def _latest_finalized(db: Session, model, service_id: uuid.UUID, statuses):
    """The highest-version FINALIZED (status in `statuses`) row of `model` for a
    service.

    Only finalized (approved/released) assessments feed the client-visible value
    summary. A released deliverable's assessment is APPROVED/RELEASED; a
    re-assessment opened AFTER release is a new higher-version DRAFT. Filtering to
    finalized statuses keeps the summary pinned to released work so a post-release
    draft can never leak its in-progress numbers to the client (§12)."""
    return db.execute(
        select(model)
        .where(model.service_id == service_id, model.status.in_(statuses))
        .order_by(model.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def _released_service_ids_by_kind(
    db: Session, client_id: uuid.UUID
) -> dict[ServiceKind, list[uuid.UUID]]:
    """Distinct service ids that have at least one RELEASED deliverable, grouped
    by service kind. This is the §12 visibility gate for the value summary."""
    rows = (
        db.execute(
            select(Service.id, Service.kind)
            .join(Deliverable, Deliverable.service_id == Service.id)
            .where(
                Service.client_id == client_id,
                Deliverable.released_at.is_not(None),
            )
            .distinct()
        )
        .tuples()
        .all()
    )
    out: dict[ServiceKind, list[uuid.UUID]] = {}
    for sid, kind in rows:
        out.setdefault(kind, []).append(sid)
    return out


def _csf_gap_total(db: Session, service_ids: list[uuid.UUID]) -> int | None:
    if not service_ids:
        return None
    total = 0
    found = False
    for sid in service_ids:
        a = _latest_finalized(
            db,
            CsfAssessment,
            sid,
            (CsfAssessmentStatus.APPROVED, CsfAssessmentStatus.RELEASED),
        )
        if a is None:
            continue
        found = True
        rows = db.execute(select(CsfAnswer).where(CsfAnswer.assessment_id == a.id)).scalars().all()
        answers: dict[str, int | None] = {r.subcategory_code: r.maturity_tier for r in rows}
        total += csf_analyze_gaps(answers).total_gap_count
    return total if found else None


def _zt_gap_total(db: Session, service_ids: list[uuid.UUID]) -> int | None:
    if not service_ids:
        return None
    total = 0
    found = False
    for sid in service_ids:
        a = _latest_finalized(
            db,
            ZtAssessment,
            sid,
            (ZtAssessmentStatus.APPROVED, ZtAssessmentStatus.RELEASED),
        )
        if a is None:
            continue
        found = True
        fw = (
            ZtFrameworkCode.CISA_ZTMM_2_0
            if a.framework == ZtFramework.CISA_ZTMM_2_0
            else ZtFrameworkCode.DOD_ZTRA
        )
        rows = db.execute(select(ZtAnswer).where(ZtAnswer.assessment_id == a.id)).scalars().all()
        answers: dict[str, int | None] = {r.capability_code: r.maturity_stage for r in rows}
        targets: dict[str, int | None] = {r.capability_code: r.target_stage for r in rows}
        total += zt_analyze_gaps(fw, answers, targets=targets).total_gap_count
    return total if found else None


def _attack_uncovered_total(db: Session, service_ids: list[uuid.UUID]) -> int | None:
    if not service_ids:
        return None
    total = 0
    found = False
    for sid in service_ids:
        a = _latest_finalized(
            db,
            AttackAssessment,
            sid,
            (AttackAssessmentStatus.APPROVED, AttackAssessmentStatus.RELEASED),
        )
        if a is None:
            continue
        found = True
        rows = (
            db.execute(select(AttackCoverage).where(AttackCoverage.assessment_id == a.id))
            .scalars()
            .all()
        )
        coverage_map: dict[str, str | None] = {r.technique_code: r.status for r in rows}
        total += attack_compute(coverage_map).gap
    return total if found else None


def _tech_debt_savings(db: Session, service_ids: list[uuid.UUID]) -> tuple[float, bool] | None:
    """(annual savings, cost_known). Savings = sum of annual cost over CUT
    capabilities; cost_known is False when any CUT item lacked a cost (so the
    figure is a floor). Mirrors routes/tech_debt.py:consolidation_plan_summary."""
    if not service_ids:
        return None
    total = 0.0
    cost_known = True
    found = False
    for sid in service_ids:
        cl = _latest_finalized(
            db,
            CapabilityList,
            sid,
            (CapabilityListStatus.APPROVED, CapabilityListStatus.RELEASED),
        )
        if cl is None:
            continue
        found = True
        items = (
            db.execute(select(CapabilityItem).where(CapabilityItem.capability_list_id == cl.id))
            .scalars()
            .all()
        )
        for it in items:
            if it.disposition == CapabilityDisposition.CUT:
                if it.annual_cost_usd is None:
                    cost_known = False
                else:
                    total += float(it.annual_cost_usd)
    if not found:
        return None
    return (total, cost_known)


@router.get(
    "/{client_id}/value-summary",
    response_model=ValueSummaryResponse,
    summary="Cross-service executive value summary (client + admin)",
)
def value_summary(
    client_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    client: Annotated[Client, Depends(current_client)],
    db: Annotated[Session, Depends(get_db)],
) -> ValueSummaryResponse:
    # Tenant enforcement mirrors the deliverables route: 404 (never 403) so one
    # tenant can't confirm another's id exists.
    if client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )

    by_kind = _released_service_ids_by_kind(db, client.id)
    td = _tech_debt_savings(db, by_kind.get(ServiceKind.TECH_DEBT, []))
    zt_ids = by_kind.get(ServiceKind.ZERO_TRUST_CISA, []) + by_kind.get(
        ServiceKind.ZERO_TRUST_DOD, []
    )
    zt_gaps = _zt_gap_total(db, zt_ids)
    attack_uncovered = _attack_uncovered_total(db, by_kind.get(ServiceKind.ATTACK_COVERAGE, []))
    csf_gaps = _csf_gap_total(db, by_kind.get(ServiceKind.NIST_CSF, []))

    savings = td[0] if td is not None else None
    cost_known = td[1] if td is not None else True
    has_any = any(v is not None for v in (savings, zt_gaps, attack_uncovered, csf_gaps))

    _log.info(
        "client.value_summary.computed",
        client_id=str(client.id),
        actor_user_id=str(user.id),
        has_any_data=has_any,
    )
    return ValueSummaryResponse(
        tech_debt_savings_usd=savings,
        tech_debt_savings_cost_known=cost_known,
        zt_gap_count=zt_gaps,
        attack_uncovered_count=attack_uncovered,
        csf_gap_count=csf_gaps,
        has_any_data=has_any,
    )
