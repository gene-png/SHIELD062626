"""Client-portal read schemas (Sprint 5).

The client-facing view of released deliverables (Master Spec §6.7, §12). Only
released deliverables ever reach these shapes; unreleased work and drafts never
serialize here.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.service import ServiceKind


class ClientDeliverableResponse(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    service_kind: ServiceKind
    service_title: str
    title: str
    summary: str | None
    version: int
    released_at: datetime | None
    superseded: bool
    pdf_artifact_id: uuid.UUID | None
    xlsx_artifact_id: uuid.UUID | None
    docx_artifact_id: uuid.UUID | None
    pdf_filename: str | None
    xlsx_filename: str | None
    docx_filename: str | None


class ClientDeliverableListResponse(BaseModel):
    items: list[ClientDeliverableResponse]


class ValueSummaryResponse(BaseModel):
    """Cross-service executive value loop (Master Spec §2.5).

    A DETERMINISTIC synthesis of already-computed engine outputs — no LLM, no new
    scoring. Each slot is `None` until the service has a RELEASED deliverable
    (§12 visibility): the card renders "pending" for a null, never a fake number.
    `tech_debt_savings_cost_known` is False when a cut capability lacked a cost,
    so the UI can flag the savings figure as a floor.
    """

    tech_debt_savings_usd: float | None
    tech_debt_savings_cost_known: bool
    zt_gap_count: int | None
    attack_uncovered_count: int | None
    csf_gap_count: int | None
    has_any_data: bool
