"""Message schemas (Work Order C7)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    author_user_id: uuid.UUID | None
    author_role: str | None = None
    body: str
    created_at: datetime
    read_at: datetime | None


class MessageListResponse(BaseModel):
    messages: list[MessageRow]


class MessageCreateRequest(BaseModel):
    body: str
