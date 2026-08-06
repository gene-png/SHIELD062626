"""The route-side evidence join that feeds the ATT&CK deliverable (D-035).

`app/attack/exporters.py` prints "No evidence attached" only where
`evidence_artifact_id` is NULL, so the join that resolves the filename has to
fail loudly on a pointer it cannot resolve. A silent miss would turn a broken
reference into a reassuring sentence in a client document.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.artifact import Artifact, ArtifactOrigin
from app.models.attack_assessment import AttackCoverage
from app.models.client import Client
from app.routes.attack import _evidence_filenames


@pytest.fixture()
def db(tmp_path) -> Iterator[Session]:
    url = f"sqlite:///{tmp_path / 'shield-attack-evidence.db'}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url, future=True)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    try:
        yield session
    finally:
        session.close()


def _client(db: Session, name: str) -> Client:
    row = Client(legal_name=name)
    db.add(row)
    db.flush()
    return row


def _artifact(db: Session, *, client_id: uuid.UUID, filename: str) -> Artifact:
    row = Artifact(
        client_id=client_id,
        title=filename,
        file_storage_key=f"evidence/{uuid.uuid4()}/{filename}",
        mime_type="text/csv",
        size_bytes=11,
        sha256="0" * 64,
        origin=ArtifactOrigin.CLIENT_UPLOAD,
        uploaded_by=uuid.uuid4(),
    )
    db.add(row)
    db.flush()
    return row


def _coverage(evidence_artifact_id: uuid.UUID | None) -> AttackCoverage:
    return AttackCoverage(
        id=uuid.uuid4(),
        assessment_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        technique_code="T1003",
        status="partial",
        evidence_artifact_id=evidence_artifact_id,
    )


@pytest.mark.unit
def test_join_resolves_the_attached_filename(db: Session) -> None:
    tenant = _client(db, "Atlas Defense Solutions")
    art = _artifact(db, client_id=tenant.id, filename="atlas-siem-export-2026-07.csv")
    names = _evidence_filenames(db, client_id=tenant.id, rows=[_coverage(art.id)])
    assert names == {art.id: "atlas-siem-export-2026-07.csv"}


@pytest.mark.unit
def test_join_is_empty_when_no_row_cites_evidence(db: Session) -> None:
    tenant = _client(db, "Atlas Defense Solutions")
    assert _evidence_filenames(db, client_id=tenant.id, rows=[_coverage(None)]) == {}


@pytest.mark.unit
def test_join_raises_typed_conflict_on_a_dangling_pointer(db: Session) -> None:
    tenant = _client(db, "Atlas Defense Solutions")
    with pytest.raises(HTTPException) as exc:
        _evidence_filenames(db, client_id=tenant.id, rows=[_coverage(uuid.uuid4())])
    assert exc.value.status_code == 409
    assert exc.value.detail["reason"] == "evidence_artifact_missing"


@pytest.mark.unit
def test_join_will_not_resolve_another_tenants_artifact(db: Session) -> None:
    ours = _client(db, "Atlas Defense Solutions")
    theirs = _client(db, "Rook Pawn Security")
    art = _artifact(db, client_id=theirs.id, filename="not-ours.csv")
    with pytest.raises(HTTPException) as exc:
        _evidence_filenames(db, client_id=ours.id, rows=[_coverage(art.id)])
    assert exc.value.detail["reason"] == "evidence_artifact_missing"
