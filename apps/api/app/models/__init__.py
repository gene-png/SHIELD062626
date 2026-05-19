"""SQLAlchemy ORM models.

Import order matters here: importing this package registers every model
against `Base.metadata`, which Alembic autogenerate relies on.
"""

from __future__ import annotations

from app.models.artifact import Artifact, ArtifactOrigin
from app.models.audit_entry import AuditEntry
from app.models.capability import (
    CapabilityItem,
    CapabilityList,
    CapabilityListStatus,
)
from app.models.client import Client
from app.models.csf_assessment import (
    CsfAnswer,
    CsfAssessment,
    CsfAssessmentStatus,
)
from app.models.deliverable import Deliverable
from app.models.llm_call import LLMCall, LLMCallMode, LLMCallStatus
from app.models.notification import Notification
from app.models.service import Service, ServiceKind, ServiceStatus
from app.models.service_request import ServiceRequest, ServiceType
from app.models.user import User, UserRole

__all__ = [
    "Artifact",
    "ArtifactOrigin",
    "AuditEntry",
    "CapabilityItem",
    "CapabilityList",
    "CapabilityListStatus",
    "Client",
    "CsfAnswer",
    "CsfAssessment",
    "CsfAssessmentStatus",
    "Deliverable",
    "LLMCall",
    "LLMCallMode",
    "LLMCallStatus",
    "Notification",
    "Service",
    "ServiceKind",
    "ServiceRequest",
    "ServiceStatus",
    "ServiceType",
    "User",
    "UserRole",
]
