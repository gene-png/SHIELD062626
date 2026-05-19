"""Tech Debt route schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.capability import CapabilityListStatus
from app.models.service import ServiceKind, ServiceStatus


class ServiceCreateRequest(BaseModel):
    kind: ServiceKind = ServiceKind.TECH_DEBT
    title: str = Field(min_length=1, max_length=255)
    source_request_id: uuid.UUID | None = None


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ServiceKind
    status: ServiceStatus
    title: str
    source_request_id: uuid.UUID | None
    opened_by: uuid.UUID
    released_at: datetime | None
    created_at: datetime


class ExtractRequest(BaseModel):
    artifact_id: uuid.UUID


class CapabilityItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    capability_list_id: uuid.UUID
    name: str
    vendor: str | None
    category: str | None
    function: str | None
    annual_cost_usd: float | None
    license_count: int | None
    notes: str | None
    confidence_pct: int | None
    source_artifact_id: uuid.UUID | None


class CapabilityListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    version: int
    status: CapabilityListStatus
    items: list[CapabilityItemResponse]
    approved_at: datetime | None
    approved_by: uuid.UUID | None


class CapabilityItemPatch(BaseModel):
    """Partial-update body for inline edits in the admin table.

    Every field is optional so the editable table can PATCH on every blur
    without re-sending the rest of the row. Sending any field marks the row
    human-curated (clears `confidence_pct`).
    """

    name: str | None = Field(default=None, max_length=255)
    vendor: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=128)
    function: str | None = Field(default=None, max_length=255)
    annual_cost_usd: float | None = None
    license_count: int | None = None
    notes: str | None = None
