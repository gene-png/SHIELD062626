"""Phase 4 acceptance gate: end-to-end CSF assessment walk.

Full happy path: admin opens a CSF service, creates an assessment,
scores all 106 subcategories, approves, finalizes, releases. From the
engagement client's POV we verify:

  - the assessment becomes readable after release
  - the deliverable shows up under GET /deliverables (the global,
    service-kind-agnostic client list from Phase 3 stage 9)
  - the client can download PDF + XLSX bytes
  - re-release on the same day supersedes the prior version
  - score + gap stay admin-only throughout
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
    db_path = tmp_path / "shield-csfacc.db"
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


def _seed_and_release(
    c: TestClient, bearer: str, *, score_tier: int = 3
) -> tuple[str, str]:
    """Open service, create assessment, score every subcategory at
    `score_tier`, approve, finalize, release. Returns (service_id,
    deliverable_id).
    """
    sr = c.post(
        "/csf/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "nist_csf", "title": "Atlas - CSF"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/csf/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assessment = a.json()
    for ans in assessment["answers"]:
        c.patch(
            f"/csf/answers/{ans['id']}",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"maturity_tier": score_tier},
        )
    c.post(
        f"/csf/assessments/{assessment['id']}/approve",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    fin = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    deliv_id = fin.json()["id"]
    rel = c.post(
        f"/csf/deliverables/{deliv_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert rel.status_code == 200, rel.text
    return svc_id, deliv_id


@pytest.mark.unit
def test_phase4_acceptance_gate(app_client) -> None:
    """The full Phase 4 happy path from admin through to client download."""
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, deliv_id = _seed_and_release(c, bearer_admin, score_tier=3)

    # Client sees the released deliverable in the global list.
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert listing.status_code == 200
    items = listing.json()["items"]
    target = next((i for i in items if i["id"] == deliv_id), None)
    assert target is not None
    assert target["service_id"] == svc_id
    assert target["version"] == 1
    assert target["released_to_client_at"] is not None
    assert target["pdf_artifact_id"] is not None
    assert target["xlsx_artifact_id"] is not None
    assert "NIST_CSF_2_0_Assessment" in target["pdf_filename"]

    # Client can read the latest assessment now that it's released.
    assess = c.get(
        f"/csf/services/{svc_id}/assessments/latest",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert assess.status_code == 200
    assert assess.json()["status"] == "released"

    # PDF + XLSX downloads work for the client.
    pdf = c.get(
        f"/artifacts/{target['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "attachment" in pdf.headers["content-disposition"]

    xlsx = c.get(
        f"/artifacts/{target['xlsx_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"

    # Score + gap remain admin-only even after release.
    s = c.get(
        f"/csf/services/{svc_id}/score",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert s.status_code == 403
    g = c.get(
        f"/csf/services/{svc_id}/gap-analysis",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert g.status_code == 403


@pytest.mark.unit
def test_unreleased_csf_deliverable_invisible_to_client(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    # Seed but DON'T release.
    sr = c.post(
        "/csf/services",
        headers={"Authorization": f"Bearer {bearer_admin}"},
        json={"kind": "nist_csf", "title": "Atlas - CSF"},
    )
    svc_id = sr.json()["id"]
    a = c.post(
        f"/csf/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    for ans in a.json()["answers"]:
        c.patch(
            f"/csf/answers/{ans['id']}",
            headers={"Authorization": f"Bearer {bearer_admin}"},
            json={"maturity_tier": 2},
        )
    c.post(
        f"/csf/assessments/{a.json()['id']}/approve",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    fin = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    deliv_id = fin.json()["id"]

    # Not released - global list omits it.
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert all(i["id"] != deliv_id for i in listing.json()["items"])
    # Detail 404s for the client.
    detail = c.get(
        f"/deliverables/{deliv_id}",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert detail.status_code == 404
    # Client artifact download forbidden until release.
    pdf = c.get(
        f"/artifacts/{fin.json()['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert pdf.status_code == 404


@pytest.mark.unit
def test_csf_re_release_supersedes_prior_in_client_list(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    client = _register(c, "client@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    bearer_client = client["tokens"]["access_token"]

    svc_id, v1_id = _seed_and_release(c, bearer_admin, score_tier=2)

    # Re-finalize on the same day -> v2, then release it too.
    fin2 = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    v2_id = fin2.json()["id"]
    c.post(
        f"/csf/deliverables/{v2_id}/release",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )

    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    items = [i for i in listing.json()["items"] if i["service_id"] == svc_id]
    # Superseded v1 is hidden; only v2 visible.
    assert len(items) == 1
    assert items[0]["id"] == v2_id
    assert items[0]["version"] == 2
    # v1 was a real deliverable but is now masked.
    assert v1_id != v2_id


@pytest.mark.unit
def test_unknown_csf_service_404_consistently(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    unknown = _uuid.uuid4()
    paths = [
        f"/csf/services/{unknown}/assessments",
        f"/csf/services/{unknown}/assessments/latest",
        f"/csf/services/{unknown}/score",
        f"/csf/services/{unknown}/gap-analysis",
        f"/csf/services/{unknown}/deliverables/finalize",
        f"/csf/services/{unknown}/deliverables/latest",
    ]
    for path in paths:
        method = "POST" if path.endswith("/assessments") or path.endswith("/finalize") else "GET"
        r = c.request(
            method,
            path,
            headers={"Authorization": f"Bearer {bearer}"},
        )
        assert r.status_code == 404, f"{path} returned {r.status_code}"
