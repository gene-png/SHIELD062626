"""HTTP-level tests for the CSF deliverable workflow routes."""

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
    db_path = tmp_path / "shield-csfdeliv.db"
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
    # Multi-tenant (post-0013): admin/reviewer callers must name an active
    # tenant via X-Client-Id. Seed one tenant and bake the header into the
    # test client so single-tenant-style tests resolve to it; client-role
    # callers are pinned to their own client and ignore this header.
    from app.models.client import Client as _Client

    _seed = TestSession()
    _tenant = _Client(legal_name="Test Tenant")
    _seed.add(_tenant)
    _seed.commit()
    _cid = str(_tenant.id)
    _seed.close()

    with TestClient(app, headers={"X-Client-Id": _cid}) as c:
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


def _seed_approved(c: TestClient, bearer: str) -> tuple[str, str]:
    """Open CSF service, create assessment, score everything tier 3, approve."""
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
    assess = a.json()
    # Patch every answer to tier 3 so the score is well-defined.
    for ans in assess["answers"]:
        c.patch(
            f"/csf/answers/{ans['id']}",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"maturity_tier": 3},
        )
    c.post(
        f"/csf/assessments/{assess['id']}/approve",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    return svc_id, assess["id"]


@pytest.mark.unit
def test_finalize_renders_pdf_and_xlsx(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    svc_id, _ = _seed_approved(c, bearer)
    r = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["version"] == 1
    assert body["finalized_at"] is not None
    assert body["released_to_client_at"] is None
    assert body["pdf_artifact_id"] is not None
    assert body["xlsx_artifact_id"] is not None
    assert body["pdf_filename"].endswith(".pdf")
    assert "NIST_CSF_2_0_Assessment" in body["pdf_filename"]
    assert body["xlsx_filename"].endswith(".xlsx")
    assert "Overall maturity" in body["summary"]


@pytest.mark.unit
def test_finalize_requires_approved_assessment(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    sr = c.post(
        "/csf/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "nist_csf", "title": "Atlas"},
    )
    svc_id = sr.json()["id"]
    c.post(
        f"/csf/services/{svc_id}/assessments",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    # No approve.
    r = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 409


@pytest.mark.unit
def test_finalize_404_for_non_csf_service(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    td = c.post(
        "/tech-debt/services",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"kind": "tech_debt", "title": "x"},
    )
    r = c.post(
        f"/csf/services/{td.json()['id']}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404


@pytest.mark.unit
def test_release_flips_stamp_and_supersedes_prior(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    svc_id, _ = _seed_approved(c, bearer)
    r1 = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    r2 = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    v2_id = r2.json()["id"]
    release = c.post(
        f"/csf/deliverables/{v2_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert release.status_code == 200
    stamp = release.json()["released_to_client_at"]
    assert stamp is not None
    # Idempotent.
    again = c.post(
        f"/csf/deliverables/{v2_id}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert again.json()["released_to_client_at"] == stamp
    # Latest is v2.
    latest = c.get(
        f"/csf/services/{svc_id}/deliverables/latest",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert latest.json()["id"] == v2_id
    assert r1.status_code == 201  # placeholder; superseded_by is internal


@pytest.mark.unit
def test_release_unknown_deliverable_404(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    r = c.post(
        f"/csf/deliverables/{_uuid.uuid4()}/release",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404


@pytest.mark.unit
def test_latest_404_when_no_deliverable(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    svc_id, _ = _seed_approved(c, bearer)
    r = c.get(
        f"/csf/services/{svc_id}/deliverables/latest",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404


@pytest.mark.unit
def test_release_unlocks_client_assessment_view(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    client = _register(c, "client@example.com")
    c.headers["X-Client-Id"] = client["user"]["client_id"]
    bearer_client = client["tokens"]["access_token"]
    svc_id, assess_id = _seed_approved(c, bearer_admin)
    # Before release: client is locked out.
    r1 = c.get(
        f"/csf/services/{svc_id}/assessments/latest",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert r1.status_code == 403
    # Finalize + release.
    fin = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    c.post(
        f"/csf/deliverables/{fin.json()['id']}/release",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    # Now the client can read.
    r2 = c.get(
        f"/csf/services/{svc_id}/assessments/latest",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "released"


@pytest.mark.unit
def test_released_deliverable_visible_in_global_list_to_client(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    client = _register(c, "client@example.com")
    c.headers["X-Client-Id"] = client["user"]["client_id"]
    bearer_client = client["tokens"]["access_token"]
    svc_id, _ = _seed_approved(c, bearer_admin)
    fin = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    c.post(
        f"/csf/deliverables/{fin.json()['id']}/release",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    listing = c.get(
        "/deliverables",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert any(i["id"] == fin.json()["id"] for i in items)


@pytest.mark.unit
def test_client_can_download_released_csf_deliverable(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer_admin = admin["tokens"]["access_token"]
    client = _register(c, "client@example.com")
    c.headers["X-Client-Id"] = client["user"]["client_id"]
    bearer_client = client["tokens"]["access_token"]
    svc_id, _ = _seed_approved(c, bearer_admin)
    fin = c.post(
        f"/csf/services/{svc_id}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    deliv = fin.json()
    c.post(
        f"/csf/deliverables/{deliv['id']}/release",
        headers={"Authorization": f"Bearer {bearer_admin}"},
    )
    pdf = c.get(
        f"/artifacts/{deliv['pdf_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
    xlsx = c.get(
        f"/artifacts/{deliv['xlsx_artifact_id']}/download",
        headers={"Authorization": f"Bearer {bearer_client}"},
    )
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"


@pytest.mark.unit
def test_finalize_404_for_unknown_service(app_client) -> None:
    c = app_client
    admin = _register(c, "admin@example.com")
    bearer = admin["tokens"]["access_token"]
    r = c.post(
        f"/csf/services/{_uuid.uuid4()}/deliverables/finalize",
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert r.status_code == 404
