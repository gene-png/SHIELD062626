"""Smoke tests for the CSF PDF + XLSX exporters."""

from __future__ import annotations

import io
import uuid

import pytest

from app.csf.catalog import SUBCATEGORIES
from app.csf.exporters import build_context, render_docx, render_pdf, render_xlsx
from app.csf.gap import analyze as analyze_gaps
from app.csf.maturity import TIER_DEFINITIONS
from app.csf.scoring import compute as compute_score
from app.models.csf_assessment import CsfAnswer, CsfAssessment, CsfAssessmentStatus
from app.models.csf_profile import CsfGapAction


def _build_inputs(*, answers_tier: int | None = 3) -> tuple[CsfAssessment, list[CsfAnswer]]:
    a = CsfAssessment(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        version=1,
        status=CsfAssessmentStatus.APPROVED,
    )
    answers = []
    for sc in SUBCATEGORIES:
        ans = CsfAnswer(
            id=uuid.uuid4(),
            assessment_id=a.id,
            subcategory_code=sc.code,
            maturity_tier=answers_tier,
        )
        answers.append(ans)
    return a, answers


@pytest.fixture()
def context_with_full_tier3():
    a, answers = _build_inputs(answers_tier=3)
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    score = compute_score(tier_map)
    gap = analyze_gaps(tier_map, target_tier=4)  # everything is below T4
    return build_context(
        client_legal_name="Atlas Defense Solutions",
        service_title="NIST CSF 2.0 Assessment",
        assessment=a,
        answers=answers,
        score=score,
        gap=gap,
    )


@pytest.mark.unit
def test_xlsx_render_has_three_sheets(context_with_full_tier3) -> None:
    from openpyxl import load_workbook

    raw = render_xlsx(context_with_full_tier3)
    assert isinstance(raw, bytes)
    assert raw[:2] == b"PK"  # XLSX is a zip envelope
    wb = load_workbook(io.BytesIO(raw))
    assert set(wb.sheetnames) == {"Score Summary", "Answers", "Gap Plan"}


@pytest.mark.unit
def test_xlsx_score_summary_carries_overall_label(context_with_full_tier3) -> None:
    from openpyxl import load_workbook

    raw = render_xlsx(context_with_full_tier3)
    wb = load_workbook(io.BytesIO(raw))
    ws = wb["Score Summary"]
    cells = [(ws.cell(row=r, column=1).value, ws.cell(row=r, column=2).value) for r in range(1, 7)]
    label = dict(cells).get("Overall maturity")
    # All tier 3 -> Repeatable.
    assert label == "Repeatable"


@pytest.mark.unit
def test_xlsx_answers_sheet_has_one_row_per_subcategory(context_with_full_tier3) -> None:
    from openpyxl import load_workbook

    raw = render_xlsx(context_with_full_tier3)
    wb = load_workbook(io.BytesIO(raw))
    ws = wb["Answers"]
    # 106 subcategories + 1 header = 107 rows.
    assert ws.max_row == 107


@pytest.mark.unit
def test_xlsx_gap_plan_contains_top_gaps_when_target_is_adaptive(
    context_with_full_tier3,
) -> None:
    from openpyxl import load_workbook

    raw = render_xlsx(context_with_full_tier3)
    wb = load_workbook(io.BytesIO(raw))
    ws = wb["Gap Plan"]
    # Default top_n=20 with target=4 produces 20 gap rows + 1 header.
    assert ws.max_row == 21


@pytest.mark.unit
def test_pdf_render_produces_valid_pdf(context_with_full_tier3) -> None:
    raw = render_pdf(context_with_full_tier3)
    assert isinstance(raw, bytes)
    assert raw.startswith(b"%PDF-")
    assert len(raw) > 2000


def _pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    return "".join(page.extract_text() for page in reader.pages)


@pytest.mark.unit
def test_pdf_render_carries_title_client_and_a_known_value(context_with_full_tier3) -> None:
    # SMOKE §10: upgrade from %PDF- magic to real content — title, client, and
    # one known computed value (all-tier-3 rolls up to "Repeatable").
    text = _pdf_text(render_pdf(context_with_full_tier3))
    assert "NIST CSF 2.0 Assessment" in text  # service title
    assert "Atlas Defense Solutions" in text  # client name
    assert "Repeatable" in text  # overall maturity label (tier 3)


@pytest.mark.unit
def test_pdf_handles_empty_gap_list() -> None:
    a, answers = _build_inputs(answers_tier=4)  # everyone Adaptive
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    score = compute_score(tier_map)
    # Target tier 3 means everyone is past it -> zero gaps.
    gap = analyze_gaps(tier_map, target_tier=3)
    assert gap.total_gap_count == 0
    ctx = build_context(
        client_legal_name=None,
        service_title="x",
        assessment=a,
        answers=answers,
        score=score,
        gap=gap,
    )
    raw = render_pdf(ctx)
    assert raw.startswith(b"%PDF-")


@pytest.mark.unit
def test_xlsx_handles_empty_gap_list_with_placeholder_row() -> None:
    from openpyxl import load_workbook

    a, answers = _build_inputs(answers_tier=4)
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    score = compute_score(tier_map)
    gap = analyze_gaps(tier_map, target_tier=3)
    ctx = build_context(
        client_legal_name=None,
        service_title="x",
        assessment=a,
        answers=answers,
        score=score,
        gap=gap,
    )
    wb = load_workbook(io.BytesIO(render_xlsx(ctx)))
    ws = wb["Gap Plan"]
    # Header + 1 placeholder row.
    assert ws.max_row == 2
    assert ws.cell(row=2, column=4).value == "No gaps at target tier"


@pytest.mark.unit
def test_build_context_falls_back_to_client_when_legal_name_is_none() -> None:
    a, answers = _build_inputs()
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    score = compute_score(tier_map)
    gap = analyze_gaps(tier_map)
    ctx = build_context(
        client_legal_name=None,
        service_title="x",
        assessment=a,
        answers=answers,
        score=score,
        gap=gap,
    )
    assert ctx.client_legal_name == "Client"


@pytest.mark.unit
def test_pdf_escapes_ampersand_in_header() -> None:
    # The header lines feed reportlab Paragraph markup: a bare "&" in the
    # client name must be escaped so it renders literally instead of
    # re-emitting as an unknown entity with a synthesized semicolon.
    a, answers = _build_inputs(answers_tier=3)
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    score = compute_score(tier_map)
    gap = analyze_gaps(tier_map, target_tier=4)
    ctx = build_context(
        client_legal_name="Rook&Pawn Security",
        service_title="NIST CSF 2.0",
        assessment=a,
        answers=answers,
        score=score,
        gap=gap,
    )
    text = _pdf_text(render_pdf(ctx))
    assert "Rook&Pawn Security" in text


# ---------------------------------------------------------------------------
# S3: POA&M action plan, tier-model methodology, heatmap fills, evidence
# ---------------------------------------------------------------------------


def _pdf_norm(raw: bytes) -> str:
    """Extracted PDF text with reportlab's line wraps collapsed to spaces."""
    return " ".join(_pdf_text(raw).split())


def _docx_norm(raw: bytes) -> str:
    """Every DOCX paragraph AND table cell, wraps collapsed. Tables are not in
    `Document.paragraphs`, so a paragraph-only reader cannot see the Action
    Plan rows at all."""
    from docx import Document

    doc = Document(io.BytesIO(raw))
    chunks = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            chunks.extend(cell.text for cell in row.cells)
    return " ".join(" ".join(chunks).split())


def _action(code: str, **fields) -> CsfGapAction:
    return CsfGapAction(id=uuid.uuid4(), subcategory_code=code, **fields)


def _ctx_with_actions(actions: dict[str, CsfGapAction] | None = None, **kw):
    """All-tier-3 answers against a T4 target, so every subcategory is a gap."""
    a, answers = _build_inputs(answers_tier=3)
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    return build_context(
        client_legal_name="Atlas Defense Solutions",
        service_title="NIST CSF 2.0 Assessment",
        assessment=a,
        answers=answers,
        score=compute_score(tier_map),
        gap=analyze_gaps(tier_map, target_tier=4),
        actions=actions or {},
        **kw,
    )


GAP_PLAN_HEADERS = [
    "Subcategory",
    "Function",
    "Category",
    "Name",
    "Current tier",
    "Target tier",
    "Gap size",
    "Priority",
    "Characterization",
    "Owner",
    "Deadline",
    "Resources",
    "Success criteria",
    "POA&M ref",
    "Notes",
]


@pytest.mark.unit
def test_xlsx_gap_plan_header_contract() -> None:
    from openpyxl import load_workbook

    ws = load_workbook(io.BytesIO(render_xlsx(_ctx_with_actions())))["Gap Plan"]
    got = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    assert got == GAP_PLAN_HEADERS


@pytest.mark.unit
def test_xlsx_gap_plan_renders_an_action_rows_owner_and_deadline() -> None:
    from openpyxl import load_workbook

    ctx = _ctx_with_actions()
    code = ctx.gap.gaps[0].code
    ctx = _ctx_with_actions(
        {
            code: _action(
                code,
                characterization="mitigate",
                owner="Priya Raman, CISO",
                deadline="2026-11-30",
                resources="2 FTE, $40k tooling",
                success_criteria="Policy approved and evidenced org-wide",
                poam_ref="POAM-2026-014",
            )
        }
    )
    ws = load_workbook(io.BytesIO(render_xlsx(ctx)))["Gap Plan"]
    row = [ws.cell(row=2, column=c).value for c in range(1, ws.max_column + 1)]
    assert row[0] == code
    cells = dict(zip(GAP_PLAN_HEADERS, row, strict=True))
    assert cells["Owner"] == "Priya Raman, CISO"
    assert cells["Deadline"] == "2026-11-30"
    assert cells["Characterization"] == "mitigate"
    assert cells["Resources"] == "2 FTE, $40k tooling"
    assert cells["Success criteria"] == "Policy approved and evidenced org-wide"
    assert cells["POA&M ref"] == "POAM-2026-014"


@pytest.mark.unit
def test_xlsx_gap_plan_priority_override_wins_over_the_computed_score() -> None:
    from openpyxl import load_workbook

    base = _ctx_with_actions()
    top = base.gap.gaps[0]
    computed = f"{top.priority_score:.2f}"
    # The assertion is only meaningful if the two values differ.
    assert computed != "P1", "fixture is vacuous: computed priority already reads P1"
    plain = load_workbook(io.BytesIO(render_xlsx(base)))["Gap Plan"]
    assert plain.cell(row=2, column=8).value == computed

    ctx = _ctx_with_actions({top.code: _action(top.code, priority_override="P1")})
    ws = load_workbook(io.BytesIO(render_xlsx(ctx)))["Gap Plan"]
    assert ws.cell(row=2, column=1).value == top.code
    assert ws.cell(row=2, column=8).value == "P1"


@pytest.mark.unit
def test_pdf_carries_the_tier_model_methodology_and_a_next_step_line() -> None:
    text = _pdf_norm(render_pdf(_ctx_with_actions()))
    partial = TIER_DEFINITIONS[0]
    adaptive = TIER_DEFINITIONS[-1]
    assert f"Tier 1 — {partial.short_label}" in text
    assert " ".join(partial.description.split()) in text
    assert " ".join(adaptive.description.split()) in text
    # Computed in Python from the gap rows: 20 shown gaps, all 1 tier short.
    assert (
        "Start with the 20 subcategory gap(s) sitting 1 tier(s) below target "
        "T4 (Adaptive) — they carry the largest lift." in text
    )
    assert "0 of 20 gap(s) in this action plan name an owner; assign the remaining 20." in text


@pytest.mark.unit
def test_docx_carries_the_action_plan_the_tier_model_and_a_next_step_line() -> None:
    ctx = _ctx_with_actions()
    code = ctx.gap.gaps[0].code
    ctx = _ctx_with_actions({code: _action(code, owner="Priya Raman, CISO", deadline="2026-11-30")})
    raw = render_docx(ctx)
    assert raw[:2] == b"PK"
    text = _docx_norm(raw)
    assert "Action plan" in text
    assert f"Tier 4 — {TIER_DEFINITIONS[-1].short_label}" in text
    assert " ".join(TIER_DEFINITIONS[-1].description.split()) in text
    assert (
        "Start with the 20 subcategory gap(s) sitting 1 tier(s) below target "
        "T4 (Adaptive) — they carry the largest lift." in text
    )
    assert "1 of 20 gap(s) in this action plan name an owner; assign the remaining 19." in text
    assert "Priya Raman, CISO" in text
    assert "2026-11-30" in text


@pytest.mark.unit
def test_next_steps_report_the_zero_gap_state() -> None:
    a, answers = _build_inputs(answers_tier=4)
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    ctx = build_context(
        client_legal_name="Atlas Defense Solutions",
        service_title="NIST CSF 2.0 Assessment",
        assessment=a,
        answers=answers,
        score=compute_score(tier_map),
        gap=analyze_gaps(tier_map, target_tier=3),
    )
    expected = (
        "No subcategory scored below target T3 (Repeatable) — maintain the current "
        "controls and re-assess on the next cycle."
    )
    assert expected in _pdf_norm(render_pdf(ctx))
    assert expected in _docx_norm(render_docx(ctx))


@pytest.mark.unit
def test_xlsx_answers_tier_cells_carry_the_graded_fill() -> None:
    from openpyxl import load_workbook

    from app import export_style

    ws = load_workbook(io.BytesIO(render_xlsx(_ctx_with_actions())))["Answers"]
    want = "FF" + export_style.graded_hex(3, 4).lstrip("#").upper()
    cell = ws.cell(row=2, column=6)
    assert cell.value == 3
    assert cell.fill.start_color.rgb == want
    # A different tier must produce a different fill, or the ramp is inert.
    assert want != "FF" + export_style.graded_hex(1, 4).lstrip("#").upper()


@pytest.mark.unit
def test_xlsx_unscored_answer_rows_carry_no_fill() -> None:
    from openpyxl import load_workbook

    a, answers = _build_inputs(answers_tier=None)
    tier_map = {ans.subcategory_code: None for ans in answers}
    ctx = build_context(
        client_legal_name=None,
        service_title="x",
        assessment=a,
        answers=answers,
        score=compute_score(tier_map),
        gap=analyze_gaps(tier_map),
    )
    ws = load_workbook(io.BytesIO(render_xlsx(ctx)))["Answers"]
    assert ws.cell(row=2, column=7).value == "Unscored"
    assert ws.cell(row=2, column=6).fill.fill_type is None
    # The row still reaches the Evidence column, so "no tier" is not "no row".
    assert ws.cell(row=2, column=9).value == "No evidence attached"


@pytest.mark.unit
def test_xlsx_per_function_average_tier_cells_carry_the_graded_fill() -> None:
    from openpyxl import load_workbook

    from app import export_style

    ws = load_workbook(io.BytesIO(render_xlsx(_ctx_with_actions())))["Score Summary"]
    want = "FF" + export_style.graded_hex(3, 4).lstrip("#").upper()
    # Rows 1-6 metadata, 7 blank, 8 header, 9+ the six functions.
    assert ws.cell(row=8, column=6).value == "Average tier"
    for r in range(9, 15):
        cell = ws.cell(row=r, column=6)
        assert cell.value == "3.00", f"row {r} is not the all-tier-3 average"
        assert cell.fill.start_color.rgb == want, f"row {r} carries no graded fill"


@pytest.mark.unit
def test_xlsx_answers_evidence_renders_the_attached_filename() -> None:
    from openpyxl import load_workbook

    artifact_id = uuid.uuid4()
    a, answers = _build_inputs(answers_tier=3)
    answers[0].evidence_artifact_id = artifact_id
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    ctx = build_context(
        client_legal_name="Atlas Defense Solutions",
        service_title="x",
        assessment=a,
        answers=answers,
        score=compute_score(tier_map),
        gap=analyze_gaps(tier_map, target_tier=4),
        evidence_names={artifact_id: "gv-oc-01-charter-2026.pdf"},
    )
    ws = load_workbook(io.BytesIO(render_xlsx(ctx)))["Answers"]
    assert ws.cell(row=1, column=9).value == "Evidence"
    row = {ws.cell(row=r, column=1).value: r for r in range(2, ws.max_row + 1)}
    assert ws.cell(row=row[answers[0].subcategory_code], column=9).value == (
        "gv-oc-01-charter-2026.pdf"
    )


@pytest.mark.unit
def test_xlsx_answers_evidence_renders_the_null_sentence() -> None:
    from openpyxl import load_workbook

    ws = load_workbook(io.BytesIO(render_xlsx(_ctx_with_actions())))["Answers"]
    assert ws.cell(row=2, column=9).value == "No evidence attached"


@pytest.mark.unit
def test_build_context_refuses_an_unresolved_evidence_pointer() -> None:
    """FAIL LOUDLY: a dangling pointer must never degrade into the NULL sentence."""
    a, answers = _build_inputs(answers_tier=3)
    answers[0].evidence_artifact_id = uuid.uuid4()
    tier_map = {ans.subcategory_code: ans.maturity_tier for ans in answers}
    with pytest.raises(ValueError, match="evidence_names is missing"):
        build_context(
            client_legal_name="Atlas Defense Solutions",
            service_title="x",
            assessment=a,
            answers=answers,
            score=compute_score(tier_map),
            gap=analyze_gaps(tier_map, target_tier=4),
            evidence_names={},
        )
