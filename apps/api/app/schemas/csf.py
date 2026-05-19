"""NIST CSF 2.0 route schemas (Phase 4 stage 2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.csf_assessment import CsfAssessmentStatus
from app.models.service import ServiceKind, ServiceStatus

# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


class CatalogSubcategory(BaseModel):
    code: str
    function: str
    category: str
    name: str
    outcome: str


class CatalogCategory(BaseModel):
    code: str
    function: str
    name: str
    purpose: str
    subcategories: list[CatalogSubcategory]


class CatalogFunction(BaseModel):
    code: str
    name: str
    purpose: str
    categories: list[CatalogCategory]


class CatalogTier(BaseModel):
    tier: int
    short_label: str
    description: str


class CatalogResponse(BaseModel):
    """Returned by GET /csf/catalog. Static reference data."""

    functions: list[CatalogFunction]
    tiers: list[CatalogTier]
    total_subcategories: int


# ---------------------------------------------------------------------------
# Assessment + answers
# ---------------------------------------------------------------------------


class CsfServiceCreateRequest(BaseModel):
    kind: ServiceKind = ServiceKind.NIST_CSF
    title: str = Field(min_length=1, max_length=255)
    source_request_id: uuid.UUID | None = None


class CsfServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ServiceKind
    status: ServiceStatus
    title: str
    source_request_id: uuid.UUID | None
    opened_by: uuid.UUID
    released_at: datetime | None
    created_at: datetime


class CsfAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    subcategory_code: str
    maturity_tier: int | None
    notes: str | None
    evidence_artifact_id: uuid.UUID | None
    answered_by: uuid.UUID | None
    answered_at: datetime | None


class CsfAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    version: int
    status: CsfAssessmentStatus
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    answers: list[CsfAnswerResponse]


class CsfAnswerPatch(BaseModel):
    """Partial-update body for a single subcategory answer.

    Sending `maturity_tier: null` clears the score (returns it to
    "unscored" for the unanswered-count math).
    """

    maturity_tier: int | None = Field(default=None, ge=1, le=4)
    notes: str | None = Field(default=None, max_length=8000)
    evidence_artifact_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Scoring summary
# ---------------------------------------------------------------------------


class FunctionScore(BaseModel):
    function: str
    function_name: str
    subcategory_count: int
    answered_count: int
    average_tier: float | None
    coverage_pct: float  # answered / total * 100
    weakest_subcategory_codes: list[str]


class CsfScoreSummary(BaseModel):
    assessment_id: uuid.UUID
    version: int
    total_subcategories: int
    answered_subcategories: int
    coverage_pct: float
    average_tier: float | None
    overall_maturity_label: str
    by_function: list[FunctionScore]


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------


class GapItem(BaseModel):
    code: str
    function: str
    function_name: str
    category: str
    name: str
    outcome: str
    current_tier: int
    target_tier: int
    gap_size: int
    priority_score: float
    notes: str | None


class GapAnalysisResponse(BaseModel):
    assessment_id: uuid.UUID
    version: int
    target_tier: int
    target_label: str
    total_gap_count: int
    unscored_count: int
    gap_count_by_function: dict[str, int]
    gaps: list[GapItem]
