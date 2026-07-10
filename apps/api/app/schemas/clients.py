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
