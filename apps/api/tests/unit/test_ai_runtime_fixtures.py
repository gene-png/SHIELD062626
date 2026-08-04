"""Runtime fixture-mode AI: all 5 purposes registered, parseable, 503 on miss.

T6b: fixture mode must make the demo/dev stack exercisable OFFLINE. These tests
drive the runtime provider directly (via build_runtime_provider / from_settings)
WITHOUT any pytest FastAPI dependency overrides, proving the provider the app
actually builds in fixture mode carries a deterministic response for every job.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.ai.engine import run_job
from app.ai.fixtures import (
    _CSF_DIMENSIONS,
    _MITRE_STATUS_CYCLE,
    ALL_PURPOSES,
    MissingFixtureError,
    RuntimeFixtureProvider,
    _fixture_csf_score,
    _fixture_mitre_map,
    _fixture_zt_score,
    build_runtime_provider,
)
from app.ai.llm import LLMClient
from app.config import Settings
from app.models.llm_call import LLMCall, LLMCallStatus


@pytest.fixture()
def db_session(tmp_path) -> Iterator[Session]:
    url = f"sqlite:///{tmp_path / 'shield-runtime-fixtures.db'}"
    os.environ["DATABASE_URL"] = url
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url, future=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.unit
def test_runtime_provider_registers_all_five_purposes() -> None:
    provider = build_runtime_provider()
    assert set(provider._fixtures) >= set(ALL_PURPOSES)
    assert len(ALL_PURPOSES) == 5


@pytest.mark.unit
def test_from_settings_fixture_mode_uses_runtime_provider() -> None:
    """The provider the app builds in fixture mode is the preloaded runtime one."""
    settings = Settings(shield_llm_mode="fixture")
    client = LLMClient.from_settings(settings)
    assert isinstance(client.provider, RuntimeFixtureProvider)
    assert set(client.provider._fixtures) >= set(ALL_PURPOSES)


@pytest.mark.unit
def test_run_job_mitre_map_is_parseable_without_overrides(db_session) -> None:
    llm = LLMClient(build_runtime_provider())
    result = run_job(
        db_session,
        llm,
        "mitre_map",
        inputs={
            "capability_list": ["CrowdStrike Falcon", "Splunk"],
            "technique_codes": ["T1003", "T1059", "T1566"],
        },
        requested_by=uuid.uuid4(),
    )
    assert isinstance(result.data, dict)
    techniques = result.data["techniques"]
    assert len(techniques) == 3
    codes = {t["technique_code"] for t in techniques}
    assert codes == {"T1003", "T1059", "T1566"}
    # Every drafted technique carries a status; cited tools come only from the
    # supplied capability list.
    for t in techniques:
        assert t["status"] in {"covered", "partial", "gap", "not_applicable"}
        for cited in t["detection_tools"] + t["response_tools"]:
            assert cited in {"CrowdStrike Falcon", "Splunk"}
    row = db_session.execute(select(LLMCall)).scalars().one()
    assert row.purpose == "mitre_map"
    assert row.status == LLMCallStatus.COMPLETED


@pytest.mark.unit
def test_run_job_zt_score_cisa_is_parseable_without_overrides(db_session) -> None:
    llm = LLMClient(build_runtime_provider())
    result = run_job(
        db_session,
        llm,
        "zt_score",
        inputs={"framework": "cisa_ztmm_2_0", "capabilities": ["ID.1", "ID.2", "DE.1"]},
        requested_by=uuid.uuid4(),
    )
    assert isinstance(result.data, dict)
    caps = result.data["capabilities"]
    assert {c["code"] for c in caps} == {"ID.1", "ID.2", "DE.1"}
    for c in caps:
        assert 1 <= c["current"] <= 4
        assert 1 <= c["target"] <= 4


@pytest.mark.unit
def test_zt_score_dod_respects_three_stage_clamp(db_session) -> None:
    """DoD ZTRA maxes at stage 3; the fixture must never emit a 4."""
    llm = LLMClient(build_runtime_provider())
    result = run_job(
        db_session,
        llm,
        "zt_score",
        inputs={"framework": "dod_ztra", "capabilities": ["ID.1", "ID.2", "AC.1"]},
        requested_by=uuid.uuid4(),
    )
    caps = result.data["capabilities"]
    assert caps, "expected at least one drafted capability"
    for c in caps:
        assert 1 <= c["current"] <= 3
        assert 1 <= c["target"] <= 3


@pytest.mark.unit
def test_all_purposes_return_valid_json_for_their_parser(db_session) -> None:
    """Every purpose produces a result its job parser accepts (no raw crash)."""
    llm = LLMClient(build_runtime_provider())
    cases = {
        "mitre_map": {"technique_codes": ["T1003"], "capability_list": ["Splunk"]},
        "zt_score": {"framework": "cisa_ztmm_2_0", "capabilities": ["ID.1"]},
        "csf_score": {"tiers": ["high"], "subcategories": ["GV.OC-01"]},
        "tech_debt_extract": {"rows": [{"name": "Okta"}], "context": {}},
        "risk_synthesize": {
            "findings": [{"source": "coverage_finding", "source_id": "T1003", "kind": "attack"}],
            "valid_techniques": ["T1003"],
            "valid_controls": [],
        },
    }
    for job_name, inputs in cases.items():
        result = run_job(db_session, llm, job_name, inputs=inputs, requested_by=uuid.uuid4())
        assert result.data is not None
    # tech_debt parser returns a list of ExtractedCapability; the others dicts.
    td = run_job(
        db_session,
        llm,
        "tech_debt_extract",
        inputs={"rows": [{"name": "Okta"}], "context": {}},
        requested_by=uuid.uuid4(),
    )
    assert td.data and td.data[0].confidence_pct is not None


def _body(response) -> dict:
    return json.loads(response.content)


@pytest.mark.unit
def test_frozen_fixture_cycles_and_arithmetic_are_unchanged() -> None:
    """Sprint 10 S5 landmine pin: fixture PROSE may deepen, the values may not.

    Four e2e specs (s4-techdebt, s5-attack, s6-zt, s7-csf-playbook) assert on
    these exact deterministic values. ``_MITRE_STATUS_CYCLE``, the ZT
    current/target arithmetic and the CSF dimension arithmetic are byte-frozen:
    a change here breaks the suite, so this test states the values literally
    instead of re-deriving them from the code under test.
    """
    assert _MITRE_STATUS_CYCLE == ("covered", "partial", "gap", "covered", "not_applicable")
    assert _CSF_DIMENSIONS == (
        "governance",
        "policy",
        "implementation",
        "monitoring",
        "improvement",
    )

    # --- mitre_map: status per sorted position, citations, empty prevention ---
    mitre = _body(
        _fixture_mitre_map(
            {
                "technique_codes": ["T1001", "T1002", "T1003", "T1004", "T1005", "T1006"],
                "capability_list": ["CrowdStrike Falcon", "Splunk Enterprise"],
            }
        )
    )
    assert [(t["technique_code"], t["status"]) for t in mitre["techniques"]] == [
        ("T1001", "covered"),
        ("T1002", "partial"),
        ("T1003", "gap"),
        ("T1004", "covered"),
        ("T1005", "not_applicable"),
        ("T1006", "covered"),
    ]
    assert [t["detection_tools"] for t in mitre["techniques"]] == [
        ["CrowdStrike Falcon"],
        ["Splunk Enterprise"],
        [],
        ["Splunk Enterprise"],
        [],
        ["Splunk Enterprise"],
    ]
    assert [t["response_tools"] for t in mitre["techniques"]] == [
        ["Splunk Enterprise"],
        [],
        [],
        ["CrowdStrike Falcon"],
        [],
        ["CrowdStrike Falcon"],
    ]
    assert all(t["prevention_tools"] == [] for t in mitre["techniques"])
    assert mitre["top_blind_spots"] == ["T1003"]

    # --- zt_score: current = (i % 2) + 1, target = min(current + 2, ladder) ---
    cisa = _body(
        _fixture_zt_score({"framework": "cisa_ztmm_2_0", "capabilities": ["ID.1", "ID.2", "DE.1"]})
    )
    assert [(c["code"], c["current"], c["target"]) for c in cisa["capabilities"]] == [
        ("DE.1", 1, 3),
        ("ID.1", 2, 4),
        ("ID.2", 1, 3),
    ]
    dod = _body(
        _fixture_zt_score({"framework": "dod_ztra", "capabilities": ["ID.1", "ID.2", "AC.1"]})
    )
    assert [(c["code"], c["current"], c["target"]) for c in dod["capabilities"]] == [
        ("AC.1", 1, 3),
        ("ID.1", 2, 3),
        ("ID.2", 1, 3),
    ]
    assert sorted(cisa["pillar_narratives"]) == ["DE", "ID"]

    # --- csf_score: base = (tier_index + subcat_index) % 3, dim = (base + d) % 3
    csf = _body(
        _fixture_csf_score(
            {"tiers": ["high", "moderate"], "subcategories": ["GV.OC-01", "ID.AM-01"]}
        )
    )
    assert [
        (r["tier"], r["subcategory_code"], *(r[d] for d in _CSF_DIMENSIONS)) for r in csf["scores"]
    ] == [
        ("high", "GV.OC-01", 0, 1, 2, 0, 1),
        ("high", "ID.AM-01", 1, 2, 0, 1, 2),
        ("moderate", "GV.OC-01", 1, 2, 0, 1, 2),
        ("moderate", "ID.AM-01", 2, 0, 1, 2, 0),
    ]


@pytest.mark.unit
def test_mitre_rationale_names_the_cited_tool() -> None:
    """The deepened rationale cites the same tools the row cites - by name."""
    body = _body(
        _fixture_mitre_map(
            {
                "technique_codes": ["T1001", "T1002", "T1003"],
                "capability_list": ["CrowdStrike Falcon", "Splunk Enterprise"],
            }
        )
    )
    by_code = {t["technique_code"]: t for t in body["techniques"]}

    covered = by_code["T1001"]
    assert covered["detection_tools"] == ["CrowdStrike Falcon"]
    assert covered["response_tools"] == ["Splunk Enterprise"]
    assert "CrowdStrike Falcon" in covered["rationale"]
    assert "Splunk Enterprise" in covered["rationale"]

    partial = by_code["T1002"]
    assert partial["detection_tools"] == ["Splunk Enterprise"]
    assert "Splunk Enterprise" in partial["rationale"]

    # A gap cites nothing, so the rationale must say so rather than name a tool.
    gap = by_code["T1003"]
    assert gap["detection_tools"] == [] and gap["response_tools"] == []
    assert "CrowdStrike Falcon" not in gap["rationale"]
    assert "Splunk Enterprise" not in gap["rationale"]
    assert "no detection" in gap["rationale"].lower()


@pytest.mark.unit
def test_covered_rationale_claims_no_response_play_when_none_is_cited() -> None:
    """One available tool means no response citation, so no response claim.

    The Sprint 10 defect shape in miniature: a sentence that reads as a finding
    while the half it describes cites nothing.
    """
    one_tool = _body(
        _fixture_mitre_map({"technique_codes": ["T1001"], "capability_list": ["Splunk Enterprise"]})
    )["techniques"][0]
    assert one_tool["status"] == "covered"
    assert one_tool["response_tools"] == []
    assert "no response play is cited" in one_tool["rationale"]
    assert "a response play is named" not in one_tool["rationale"]

    two_tools = _body(
        _fixture_mitre_map(
            {"technique_codes": ["T1001"], "capability_list": ["Splunk Enterprise", "Wiz"]}
        )
    )["techniques"][0]
    assert two_tools["response_tools"] == ["Wiz"]
    assert "a response play is named" in two_tools["rationale"]


@pytest.mark.unit
def test_mitre_rationale_prose_pin_matches_the_e2e_spec() -> None:
    """e2e/smoke/s5-attack.spec.ts:151 pins this exact leading prose for T1001.

    The spec's regex is a partial match on the rendered Rationale paragraph, so
    this literal and that pin move together or the spec goes red.
    """
    body = _body(
        _fixture_mitre_map({"technique_codes": ["T1001"], "capability_list": ["Splunk Enterprise"]})
    )
    rationale = body["techniques"][0]["rationale"]
    assert rationale.startswith("Fixture-mode draft coverage evidence for T1001:")


@pytest.mark.unit
def test_zt_and_csf_narratives_are_substantive_prose() -> None:
    """Deepened prose: the narratives read as evidence, not as a placeholder."""
    zt = _body(_fixture_zt_score({"framework": "cisa_ztmm_2_0", "capabilities": ["ID.1", "DE.1"]}))
    assert len(zt["roadmap_summary"]) > 120
    for pillar, narrative in zt["pillar_narratives"].items():
        assert pillar in narrative
        assert len(narrative) > 120

    csf = _body(_fixture_csf_score({"tiers": ["high"], "subcategories": ["GV.OC-01"]}))
    found = csf["scores"][0]["what_we_found"]
    assert "GV.OC-01" in found
    assert "high" in found
    assert len(found) > 120


@pytest.mark.unit
def test_missing_fixture_raises_typed_503_not_raw_keyerror(db_session) -> None:
    """A missing fixture is an operator-actionable 503, never a raw 500 KeyError."""
    provider = RuntimeFixtureProvider()  # nothing registered
    llm = LLMClient(provider)
    with pytest.raises(MissingFixtureError) as exc_info:
        run_job(
            db_session,
            llm,
            "mitre_map",
            inputs={"technique_codes": ["T1003"]},
            requested_by=uuid.uuid4(),
        )
    err = exc_info.value
    assert err.status_code == 503
    assert isinstance(err.detail, dict)
    assert err.detail["reason"] == "ai_fixture_unavailable"
    # The failed call is still audited.
    row = db_session.execute(select(LLMCall)).scalars().one()
    assert row.status == LLMCallStatus.FAILED
