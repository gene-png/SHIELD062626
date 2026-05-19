"""Client - the singleton organization served by this deployment.

Master Spec §11: single-tenant deployments hold exactly one client row.
We still keep the table because every other business table carries a
`client_id` FK to it (Master Spec §11.1: keep client_id on every row so
future multi-tenant ambitions don't require a schema migration).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ARRAY, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._common import TimestampMixin, UUIDPKMixin


class Client(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "client"

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dba_name: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))
    size_band: Mapped[str | None] = mapped_column(String(64))
    industry: Mapped[str | None] = mapped_column(String(128))

    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(128))
    state: Mapped[str | None] = mapped_column(String(64))
    postal_code: Mapped[str | None] = mapped_column(String(32))
    country: Mapped[str | None] = mapped_column(String(64))

    primary_poc_user_id: Mapped[uuid.UUID | None] = mapped_column()
    prompting_context: Mapped[str | None] = mapped_column(Text)

    service_interests: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)))
