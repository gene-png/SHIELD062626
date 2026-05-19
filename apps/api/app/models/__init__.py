"""SQLAlchemy ORM models.

Import order matters here: importing this package registers every model
against `Base.metadata`, which Alembic autogenerate relies on.
"""

from __future__ import annotations

from app.models.audit_entry import AuditEntry
from app.models.client import Client
from app.models.service_request import ServiceRequest, ServiceType
from app.models.user import User, UserRole

__all__ = [
    "AuditEntry",
    "Client",
    "ServiceRequest",
    "ServiceType",
    "User",
    "UserRole",
]
