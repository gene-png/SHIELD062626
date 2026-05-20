"""Phase 5 acceptance gate: ATT&CK Coverage end-to-end.

Walks intake -> coverage edits -> approve -> finalize -> release ->
client downloads PDF + XLSX. Plus the same supersession + unreleased-
invisibility checks the other services have.
"""

from __future__ import annotations

import os
import uuid as _uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.attack.catalog import TECHNIQUES
from app.storage.local import LocalFilesystemStorage
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def app_client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "shield-attack-acc.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    TestSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    storage = LocalFilesystemStorage(tmp_path / "storage")

    from app.db.session import get_db
    from app.main import create_app
    from app.routes.artifacts import _storage_dep

    def override_get_db() -> Iterator[Session]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[_storage_dep] = lambda: storage
    with TestClient(app) as c:
        yield c


def _register(c: TestClient, email: str) -> dict:
    r = c.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple!",
            "display_name": email.split("@")[0],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _seed_and_release(c: TestClient, bearer: str) -> tuple[str, str]:
    """Open service, create assessment, mark 5 techniques covered,
    approve, finalize, release."""
    sr = c.post(
        "/attack/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "attack_coverage", "title": "Atlas - ATT&CK Coverage"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/attack/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assessment = a.json()
    # Pick 5 rows and set them covered. Cheap proxy for "real assessor work".
    for cov in assessment["coverage"][:5]:
        c.patch(
            f"/attack/coverage/{cov['id']}",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"status": "covered"},
        )
    c.post(
        f"/attack/assessments/{assessment['id']}/approve",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    fin = c.post(
        f"/attack/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    deliv_id = fin.json()["id"]
    rel = c.post(
        f"/attack/deliverables/{deliv_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert rel.status_code == 200, rel.text
    return svc_id, deliv_id


@pytest.mark.unit
def test_phase5_attack_acceptance_gate(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, deliv_id = _seed_and_release(c, bearer_admin)

    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    target = next(
        (i for i in listing.json()["items"] if i["id"] == deliv_id), None
    )
    assert target is not None
    assert target["service_id"] == svc_id
    assert "MITRE_ATTACK_Coverage" in target["pdf_filename"]
    assert target["xlsx_filename"].endswith(".xlsx")

    # Client can read the released assessment.
    a = c.get(
        f"/attack/services/{svc_id}/assessments/latest",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert a.status_code == 200
    assert a.json()["status"] == "released"

    # PDF + XLSX downloads work for the client.
    pdf = c.get(
        f"/artifacts/{target['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
    xlsx = c.get(
        f"/artifacts/{target['xlsx_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"

    # Heatmap stays admin-only.
    h = c.get(
        f"/attack/services/{svc_id}/heatmap",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert h.status_code == 403


@pytest.mark.unit
def test_finalize_requires_approved_assessment(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    sr = c.post(
        "/attack/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "attack_coverage", "title": "x"},
    )
    svc_id = sr.json()["id"]
    c.post(
        f"/attack/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    r = c.post(
        f"/attack/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 409


@pytest.mark.unit
def test_re_release_supersedes_prior(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, v1_id = _seed_and_release(c, bearer_admin)
    fin2 = c.post(
        f"/attack/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    v2_id = fin2.json()["id"]
    c.post(
        f"/attack/deliverables/{v2_id}/release",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )

    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    items = [i for i in listing.json()["items"] if i["service_id"] == svc_id]
    assert len(items) == 1
    assert items[0]["id"] == v2_id
    assert v1_id != v2_id


@pytest.mark.unit
def test_unreleased_invisible_to_client(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    sr = c.post(
        "/attack/services",
        headers={"Authorization": f"Bearer {bearer_admin}"},
        json={"kind": "attack_coverage", "title": "x"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/attack/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    for cov in a.json()["coverage"][:3]:
        c.patch(
            f"/attack/coverage/{cov['id']}",
            headers={"Authorization": f"Bearer {bearer_admin}"},
            json={"status": "covered"},
        )
    c.post(
        f"/attack/assessments/{a.json()['id']}/approve",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    fin = c.post(
        f"/attack/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    deliv_id = fin.json()["id"]
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert all(i["id"] != deliv_id for i in listing.json()["items"])
    pdf = c.get(
        f"/artifacts/{fin.json()['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert pdf.status_code == 404


@pytest.mark.unit
def test_unknown_release_404(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    r = c.post(
        f"/attack/deliverables/{_uuid.uuid4()}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404


@pytest.mark.unit
def test_catalog_count_matches_constant() -> None:
    # Smoke - lock against accidental catalog regression.
    assert len(TECHNIQUES) >= 600
