"""Contracts for the shared deliverable style module (S1 / D-036).

Three groups:
  1. `graded_hex` — a one-hue sequential ramp that RAISES out of range.
  2. `escaped_title` — PR #50's two header fixes, in one place.
  3. Parity contracts — the geometry each exporter had before the refactor,
     pinned so a later "tidy up" cannot silently unify the margins and reflow
     every deliverable.
"""

from __future__ import annotations

import io
from html import escape

import pytest
from pypdf import PdfReader

from app import export_style

# ---------------------------------------------------------------------------
# graded_hex / graded_ink_hex
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_graded_hex_raises_out_of_range_instead_of_clamping() -> None:
    # FAIL LOUDLY: a level outside 1..n_levels is a caller bug, not something
    # to quietly pin to an end of the ramp.
    with pytest.raises(ValueError, match="level"):
        export_style.graded_hex(-1, 5)
    with pytest.raises(ValueError, match="level"):
        export_style.graded_hex(0, 5)
    with pytest.raises(ValueError, match="level"):
        export_style.graded_hex(6, 5)


@pytest.mark.unit
def test_graded_hex_raises_on_degenerate_level_count() -> None:
    with pytest.raises(ValueError, match="n_levels"):
        export_style.graded_hex(1, 1)


@pytest.mark.unit
def test_graded_hex_is_one_hue_and_monotonically_darker() -> None:
    # Sequential ramp per the house dataviz method: one hue, light -> dark.
    fills = [export_style.graded_hex(lv, 5) for lv in range(1, 6)]
    assert len(set(fills)) == 5, fills
    lums = [_rel_luminance(hx) for hx in fills]
    assert lums == sorted(lums, reverse=True), list(zip(fills, lums, strict=True))
    assert fills[-1] == export_style.BRAND_NAVY_HEX


@pytest.mark.unit
@pytest.mark.parametrize("n_levels", [2, 3, 4, 5, 7])
def test_graded_ink_meets_wcag_aa_on_every_fill(n_levels: int) -> None:
    for level in range(1, n_levels + 1):
        fill = export_style.graded_hex(level, n_levels)
        ink = export_style.graded_ink_hex(level, n_levels)
        ratio = _contrast(fill, ink)
        assert ratio >= 4.5, f"level {level}/{n_levels}: {ink} on {fill} = {ratio:.2f}:1"


@pytest.mark.unit
def test_graded_ink_hex_raises_out_of_range() -> None:
    with pytest.raises(ValueError, match="level"):
        export_style.graded_ink_hex(0, 5)
    with pytest.raises(ValueError, match="level"):
        export_style.graded_ink_hex(9, 5)


def _rel_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    chan = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        chan.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chan[0] + 0.7152 * chan[1] + 0.0722 * chan[2]


def _contrast(a: str, b: str) -> float:
    la, lb = _rel_luminance(a), _rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# escaped_title / escaped_line
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_escaped_title_escapes_ampersand_and_lt() -> None:
    assert export_style.escaped_title("MITRE ATT&CK Coverage", "Atlas") == (
        "MITRE ATT&amp;CK Coverage"
    )
    assert "&lt;" in export_style.escaped_title("Review <draft>", "Atlas")


@pytest.mark.unit
def test_escaped_title_renders_an_ampersand_org_once_escaped() -> None:
    # An org named with an ampersand renders as the escaped single-org string:
    # the "&" survives as an entity, and the org appears exactly once.
    assert export_style.escaped_title("R&D Corp", "R&D Corp") == escape("R&D Corp")
    assert export_style.escaped_title("R&D Corp", "R&D Corp") == "R&amp;D Corp"


@pytest.mark.unit
@pytest.mark.parametrize("sep", [" — ", " - ", " – ", ": "])
def test_escaped_title_never_repeats_the_org_name(sep: str) -> None:
    # Service.title is minted "{org}{sep}{label}" and the client line is
    # printed beneath the H1, so the org must not appear in both.
    title = export_style.escaped_title(f"R&D Corp{sep}Zero Trust Assessment", "R&D Corp")
    assert title == "Zero Trust Assessment"
    assert "R&amp;D" not in title
    assert "R&D" not in title


@pytest.mark.unit
def test_escaped_title_raises_on_empty_title() -> None:
    with pytest.raises(ValueError, match="service_title"):
        export_style.escaped_title("   ", "Atlas")


@pytest.mark.unit
def test_escaped_line_escapes_markup_characters() -> None:
    assert export_style.escaped_line("Rook&Pawn <Security>") == ("Rook&amp;Pawn &lt;Security&gt;")


@pytest.mark.unit
def test_metadata_title_joins_with_an_em_dash_and_does_not_escape() -> None:
    # PDF/DOCX metadata is not markup-parsed — PR #50 kept it literal.
    assert export_style.metadata_title("MITRE ATT&CK Coverage", "R&D Corp") == (
        "MITRE ATT&CK Coverage — R&D Corp"
    )


# ---------------------------------------------------------------------------
# Palette parity — the values that were scattered before S1
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_brand_hexes_match_the_design_system_tokens() -> None:
    assert export_style.INK_HEX == "#0e1220"
    assert export_style.BORDER_HEX == "#d6dae3"
    assert export_style.SURFACE_SUNKEN_HEX == "#eef2f7"
    assert export_style.BRAND_NAVY_HEX == "#1b3a7a"


@pytest.mark.unit
def test_xlsx_header_argb_is_the_sunken_surface_with_an_alpha_prefix() -> None:
    # risk/exporters.py used to hand-write "FFEEF2F7" — openpyxl's ARGB form
    # of --surface-sunken. It is now derived, not copied.
    assert export_style.XLSX_HEADER_ARGB == "FFEEF2F7"
    assert "FF" + export_style.SURFACE_SUNKEN_HEX[1:].upper() == export_style.XLSX_HEADER_ARGB


@pytest.mark.unit
def test_xlsx_header_fill_is_a_solid_sunken_fill() -> None:
    fill = export_style.xlsx_header_fill()
    assert fill.fill_type == "solid"
    assert fill.start_color.rgb == "FFEEF2F7"
    assert fill.end_color.rgb == "FFEEF2F7"


@pytest.mark.unit
def test_level_hex_relocated_unchanged_and_still_importable_from_playbook_export() -> None:
    from app.csf import playbook_export

    assert export_style.LEVEL_HEX == {
        1: "#fca5a5",
        2: "#fdba74",
        3: "#fde047",
        4: "#bef264",
        5: "#86efac",
    }
    assert playbook_export.LEVEL_HEX is export_style.LEVEL_HEX


# ---------------------------------------------------------------------------
# Page geometry parity — deliberately NOT unified
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_margin_constants_keep_the_two_geometries_apart() -> None:
    assert export_style.SERVICE_PAGE_MARGIN_IN == 0.6
    assert export_style.PLAYBOOK_PAGE_MARGIN_IN == 0.7
    assert export_style.SERVICE_PAGE_MARGIN_IN != export_style.PLAYBOOK_PAGE_MARGIN_IN


@pytest.mark.unit
@pytest.mark.parametrize("side_margin_in", [0.6, 0.7])
def test_new_pdf_doc_parameterizes_the_side_margin(side_margin_in: float) -> None:
    from reportlab.lib.units import inch

    doc = export_style.new_pdf_doc(io.BytesIO(), title="T", side_margin_in=side_margin_in)
    assert doc.leftMargin == side_margin_in * inch
    assert doc.rightMargin == side_margin_in * inch
    # Vertical margins never differed between the two families.
    assert doc.topMargin == 0.7 * inch
    assert doc.bottomMargin == 0.7 * inch


@pytest.mark.unit
def test_new_pdf_doc_rejects_a_nonpositive_margin() -> None:
    with pytest.raises(ValueError, match="side_margin_in"):
        export_style.new_pdf_doc(io.BytesIO(), title="T", side_margin_in=0)


@pytest.mark.unit
def test_service_exporters_render_at_the_service_margin() -> None:
    """Every service exporter passes SERVICE_PAGE_MARGIN_IN, the playbook does not.

    Asserted by capturing the margin `new_pdf_doc` is called with, so a change
    to any one exporter's geometry fails here rather than in a client's inbox.
    """
    seen: list[float] = []
    real = export_style.new_pdf_doc

    def spy(out, *, title, side_margin_in):  # type: ignore[no-untyped-def]
        seen.append(side_margin_in)
        return real(out, title=title, side_margin_in=side_margin_in)

    export_style.new_pdf_doc = spy  # type: ignore[assignment]
    try:
        for render, ctx in _service_pdf_cases():
            seen.clear()
            render(ctx)
            assert seen == [0.6], f"{render.__module__}: {seen}"
    finally:
        export_style.new_pdf_doc = real  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Page-count pins on a fixed context
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_service_pdf_page_counts_are_pinned() -> None:
    for render, ctx in _service_pdf_cases():
        raw = render(ctx)
        pages = len(PdfReader(io.BytesIO(raw)).pages)
        assert pages >= 1, render.__module__
        assert (
            pages == _EXPECTED_PAGES[render.__module__]
        ), f"{render.__module__} reflowed: {pages} pages"


_EXPECTED_PAGES = {
    "app.tech_debt.exporters": 1,
    "app.risk.exporters": 2,
}


def _service_pdf_cases() -> list[tuple]:
    """Two fixed contexts that need no DB — enough to pin reflow."""
    from app.risk import exporters as risk_exporters
    from app.tech_debt import exporters as td_exporters

    return [
        (td_exporters.render_pdf, _tech_debt_ctx()),
        (risk_exporters.render_pdf, _risk_ctx()),
    ]


def _tech_debt_ctx():
    import uuid

    from app.models.capability import (
        CapabilityDisposition,
        CapabilityItem,
        CapabilityList,
        CapabilityListStatus,
    )
    from app.tech_debt.exporters import build_context

    cap_list = CapabilityList(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        status=CapabilityListStatus.DRAFT,
    )
    items = [
        CapabilityItem(
            id=uuid.uuid4(),
            capability_list_id=cap_list.id,
            name="Legacy SIEM",
            vendor="Vendor A",
            category="Logging",
            annual_cost_usd=120000,
            disposition=CapabilityDisposition.CUT,
        )
    ]
    return build_context(
        client_legal_name="Atlas Defense Solutions",
        service_title="Technical Debt Review",
        cap_list=cap_list,
        items=items,
    )


def _risk_ctx():
    from types import SimpleNamespace

    from app.risk.exporters import build_context

    entry = SimpleNamespace(
        title="Unmonitored egress",
        description="No egress logging on the DMZ.",
        axis="detection",
        source="attack",
        source_id="T1041",
        linked_techniques=["T1041"],
        linked_controls=["DE.CM-01"],
        likelihood="likely",
        impact="high",
        tier="high",
        compensating_controls="",
        residual_risk="",
        recommended_action="mitigate",
        rationale="",
        origin="ai",
        trust="medium",
    )
    return build_context(client_legal_name="R&D Corp", version=3, entries=[entry])
