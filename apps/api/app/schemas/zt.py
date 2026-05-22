"""Zero Trust route schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.service import ServiceKind, ServiceStatus
from app.models.zt_assessment import ZtAssessmentStatus, ZtFramework

# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


class CatalogCapability(BaseModel):
    code: str
    pillar_code: str
    name: str
    outcome: str


class CatalogPillar(BaseModel):
    code: str
    name: str
    purpose: str
    capabilities: list[CatalogCapability]


class CatalogStage(BaseModel):
    stage: int
    label: str
    description: str


class CatalogResponse(BaseModel):
    framework: ZtFramework
    pillars: list[CatalogPillar]
    stages: list[CatalogStage]
    total_capabilities: int


# ---------------------------------------------------------------------------
# Service + assessment
# ---------------------------------------------------------------------------


class ZtServiceCreateRequest(BaseModel):
    kind: ServiceKind = Field(
        description="One of zero_trust_cisa | zero_trust_dod."
    )
    title: str = Field(min_length=1, max_length=255)
    source_request_id: uuid.UUID | None = None


class ZtServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ServiceKind
    status: ServiceStatus
    title: str
    source_request_id: uuid.UUID | None
    opened_by: uuid.UUID
    released_at: datetime | None
    created_at: datetime


class ZtAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    capability_code: str
    maturity_stage: int | None
    notes: str | None
    evidence_artifact_id: uuid.UUID | None
    answered_by: uuid.UUID | None
    answered_at: datetime | None


class ZtAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    framework: ZtFramework
    version: int
    status: ZtAssessmentStatus
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    answers: list[ZtAnswerResponse]
    # Target stage the client picked at intake (2-4), or null if not set.
    client_target_stage: int | None = None


class ZtAnswerPatch(BaseModel):
    maturity_stage: int | None = Field(default=None, ge=1, le=4)
    notes: str | None = Field(default=None, max_length=8000)
    evidence_artifact_id: uuid.UUID | None = None


class ZtSelfAssessmentSubmit(BaseModel):
    """Client submits their self-assessment for admin review.

    `target_stage` lets the client confirm/adjust the maturity goal the gap
    engine measures against; persisted on the source request.
    """

    target_stage: int | None = Field(default=None, ge=1, le=4)


# ---------------------------------------------------------------------------
# Scoring + gap
# ---------------------------------------------------------------------------


class PillarScore(BaseModel):
    pillar_code: str
    pillar_name: str
    capability_count: int
    answered_count: int
    average_stage: float | None
    coverage_pct: float
    weakest_capability_codes: list[str]


class ZtScoreSummary(BaseModel):
    assessment_id: uuid.UUID
    version: int
    framework: ZtFramework
    total_capabilities: int
    answered_capabilities: int
    coverage_pct: float
    average_stage: float | None
    overall_stage_label: str
    by_pillar: list[PillarScore]


class GapItem(BaseModel):
    code: str
    pillar_code: str
    pillar_name: str
    name: str
    outcome: str
    current_stage: int
    target_stage: int
    gap_size: int
    priority_score: float
    notes: str | None


class GapAnalysisResponse(BaseModel):
    assessment_id: uuid.UUID
    version: int
    framework: ZtFramework
    target_stage: int
    target_label: str
    total_gap_count: int
    unscored_count: int
    gap_count_by_pillar: dict[str, int]
    gaps: list[GapItem]
