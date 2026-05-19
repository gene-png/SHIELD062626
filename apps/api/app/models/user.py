"""User model.

Master Spec §11 + §2: three locked roles - admin (Kentro consultant),
reviewer (read-only auditor), client. MFA enrollment column is present
in v1 but the flag default-false until SHIELD_AUTH_REQUIRE_MFA flips on
(spec §2 locked decisions).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._common import TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    CLIENT = "client"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=False, length=16),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("client.id", ondelete="RESTRICT")
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    mfa_enrolled: Mapped[bool] = mapped_column(default=False, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
