"""ZT acceptance gate: full intake -> approve -> finalize -> release -> client download.

Runs once for CISA and once for DoD to verify both frameworks reach
client visibility through the same generic /deliverables list.
"""

from __future__ import annotations

import os
import uuid as _uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.storage.local import LocalFilesystemStorage
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def app_client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "shield-zt-acc.db"
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
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


def _seed_and_release(
    c: TestClient, bearer: str, kind: str, *, stage: int = 3
) -> tuple[str, str]:
    sr = c.post(
        "/zt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": kind, "title": f"Atlas - {kind}"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/zt/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assessment = a.json()
    for ans in assessment["answers"]:
        c.patch(
            f"/zt/answers/{ans['id']}",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"maturity_stage": stage},
        )
    c.post(
        f"/zt/assessments/{assessment['id']}/approve",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    fin = c.post(
        f"/zt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    deliv_id = fin.json()["id"]
    rel = c.post(
        f"/zt/deliverables/{deliv_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert rel.status_code == 200, rel.text
    return svc_id, deliv_id


@pytest.mark.unit
@pytest.mark.parametrize(
    "kind,framework,expected_label",
    [
        ("zero_trust_cisa", "cisa_ztmm_2_0", "Advanced"),
        ("zero_trust_dod", "dod_ztra", "Advanced"),
    ],
)
def test_phase5_zt_acceptance_gate(app_client, kind: str, framework: str, expected_label: str) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, deliv_id = _seed_and_release(c, bearer_admin, kind, stage=3)

    # Client sees the released deliverable in the global list.
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    items = listing.json()["items"]
    target = next((i for i in items if i["id"] == deliv_id), None)
    assert target is not None
    assert target["service_id"] == svc_id
    assert target["pdf_filename"].endswith(".pdf")
    assert target["xlsx_filename"].endswith(".xlsx")

    # Client can read the released assessment.
    a = c.get(
        f"/zt/services/{svc_id}/assessments/latest",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert a.status_code == 200
    assert a.json()["status"] == "released"
    assert a.json()["framework"] == framework

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

    # Score remains admin-only.
    s = c.get(
        f"/zt/services/{svc_id}/score",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert s.status_code == 403


@pytest.mark.unit
def test_finalize_requires_approved_assessment(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    sr = c.post(
        "/zt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "zero_trust_cisa", "title": "x"},
    )
    svc_id = sr.json()["id"]
    c.post(
        f"/zt/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    r = c.post(
        f"/zt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 409


@pytest.mark.unit
def test_release_supersedes_prior(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, v1_id = _seed_and_release(c, bearer_admin, "zero_trust_cisa", stage=2)

    # Re-finalize on the same day -> v2 and release.
    fin2 = c.post(
        f"/zt/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    v2_id = fin2.json()["id"]
    c.post(
        f"/zt/deliverables/{v2_id}/release",
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
        "/zt/services",
        headers={"Authorization": f"Bearer {bearer_admin}"},
        json={"kind": "zero_trust_cisa", "title": "x"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/zt/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    for ans in a.json()["answers"]:
        c.patch(
            f"/zt/answers/{ans['id']}",
            headers={"Authorization": f"Bearer {bearer_admin}"},
            json={"maturity_stage": 2},
        )
    c.post(
        f"/zt/assessments/{a.json()['id']}/approve",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    fin = c.post(
        f"/zt/services/{svc_id}/deliverables/finalize",
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
        f"/zt/deliverables/{_uuid.uuid4()}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404
