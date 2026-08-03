"""Shared deliverable styling — the single home for how SHIELD exports look (D-036).

Before S1 the same four brand hexes, the same openpyxl header fill, the same
reportlab page setup, and PR #50's inline `html.escape()` calls were copied
across six exporter modules. A palette value written six times drifts five
ways, and `risk/exporters.py` was already carrying `--surface-sunken` by hand
as `"FFEEF2F7"`.

Two things this module deliberately does NOT do:

* **It does not unify page geometry.** The four service exporters render at a
  0.6in side margin and the CSF playbook at 0.7in. Standardising them would
  reflow every deliverable and move page counts, so `new_pdf_doc()` takes the
  margin as an argument and each caller passes its own constant.
* **It does not clamp.** `graded_hex()` raises on a level outside the ramp
  rather than pinning it to an end, because a bad level is a caller bug and a
  silently-clamped colour is a lie about the data.

Brand hexes mirror `packages/design-system/src/tokens.css`; that file stays the
source of truth for the web app and this module is its export-side twin.
"""

from __future__ import annotations

import logging
from html import escape
from typing import Any

logger = logging.getLogger(__name__)
_LOG = "export_style:"

# ---------------------------------------------------------------------------
# Brand palette (packages/design-system/src/tokens.css)
# ---------------------------------------------------------------------------

INK_HEX = "#0e1220"  # --text-primary
BORDER_HEX = "#d6dae3"  # --border
SURFACE_SUNKEN_HEX = "#eef2f7"  # --surface-sunken
BRAND_NAVY_HEX = "#1b3a7a"  # --brand-navy
WHITE_HEX = "#ffffff"

# Playbook-only accents, kept here so the palette has one home.
PLAYBOOK_HEADER_HEX = "#1f2937"  # dark table header band
PLAYBOOK_ZEBRA_HEX = "#f8fafc"  # alternating row fill
PLAYBOOK_MUTED_HEX = "#64748b"  # small print

# openpyxl wants ARGB, not RGB. Derived, never hand-copied.
XLSX_HEADER_ARGB = "FF" + SURFACE_SUNKEN_HEX[1:].upper()

# CSF maturity shading, relocated from playbook_export.py (re-exported there
# for compat). Values unchanged: L1 (weakest) red -> L5 (strongest) green.
LEVEL_HEX: dict[int, str] = {
    1: "#fca5a5",
    2: "#fdba74",
    3: "#fde047",
    4: "#bef264",
    5: "#86efac",
}

# ---------------------------------------------------------------------------
# Sequential ramp
# ---------------------------------------------------------------------------

# One hue (the brand navy's), light -> dark, seven steps, per the house dataviz
# method for magnitude encoding. Built in OKLCH holding hue constant and
# landing the darkest step exactly on BRAND_NAVY_HEX; lightness is monotonic,
# so the ramp reads as ordered rather than as seven identities.
GRADED_RAMP_HEX: tuple[str, ...] = (
    "#dfeafe",
    "#b7cbf1",
    "#92adde",
    "#708fc9",
    "#5172b1",
    "#355596",
    BRAND_NAVY_HEX,
)

# The paired text colour for each fill above. Every pairing clears WCAG AA for
# normal text (4.5:1); the tightest is step 5, white on #5172b1 at 4.78:1.
GRADED_INK_HEX: tuple[str, ...] = (
    INK_HEX,
    INK_HEX,
    INK_HEX,
    INK_HEX,
    WHITE_HEX,
    WHITE_HEX,
    WHITE_HEX,
)


def _ramp_index(level: int, n_levels: int) -> int:
    """Map a 1-based level onto GRADED_RAMP_HEX, raising rather than clamping."""
    if n_levels < 2:
        raise ValueError(f"{_LOG} n_levels must be at least 2, got {n_levels!r}")
    if not 1 <= level <= n_levels:
        raise ValueError(f"{_LOG} level must be within 1..{n_levels}, got {level!r}")
    span = len(GRADED_RAMP_HEX) - 1
    return round((level - 1) / (n_levels - 1) * span)


def graded_hex(level: int, n_levels: int) -> str:
    """Fill colour for `level` of `n_levels` on the sequential navy ramp."""
    index = _ramp_index(level, n_levels)
    fill = GRADED_RAMP_HEX[index]
    logger.debug("%s graded_hex level=%s/%s -> step %s %s", _LOG, level, n_levels, index, fill)
    return fill


def graded_ink_hex(level: int, n_levels: int) -> str:
    """AA-safe text colour to print on `graded_hex(level, n_levels)`."""
    index = _ramp_index(level, n_levels)
    ink = GRADED_INK_HEX[index]
    logger.debug("%s graded_ink_hex level=%s/%s -> %s", _LOG, level, n_levels, ink)
    return ink


# ---------------------------------------------------------------------------
# Header text
# ---------------------------------------------------------------------------

# Separators a minted "{org}{sep}{label}" service title can use.
_TITLE_SEPARATORS = (" — ", " - ", " – ", ": ")


def escaped_title(service_title: str, client_name: str) -> str:
    """The H1 of a deliverable: escaped for reportlab, org name printed once.

    PR #50 fixed two header defects and S1 gives them one home:

    1. reportlab's `Paragraph` parses mini-XML, so a bare "&" (an "R&D Corp"
       client, or "MITRE ATT&CK") re-emitted as an unknown entity with a
       synthesized semicolon — the released "ATT&CK;".
    2. `Service.title` is minted "{org} - {label}" and the client line prints
       beneath the H1, so the org name appeared twice.

    A title that is *only* the org name is left alone — stripping it would
    leave an empty heading.
    """
    title = service_title.strip()
    org = client_name.strip()
    if org and title != org:
        for sep in _TITLE_SEPARATORS:
            prefix = f"{org}{sep}"
            if title.startswith(prefix):
                title = title[len(prefix) :].strip()
                logger.debug("%s dropped repeated org name from the H1", _LOG)
                break
    if not title:
        raise ValueError(f"{_LOG} service_title is empty after trimming: {service_title!r}")
    logger.debug("%s escaped_title -> %r", _LOG, title)
    return escape(title)


def escaped_line(text: str) -> str:
    """Escape a body line or table cell fed to reportlab's markup parser."""
    return escape(text)


def metadata_title(left: str, right: str) -> str:
    """The PDF/DOCX document-properties title. Not markup-parsed, so literal."""
    return f"{left} — {right}"


# ---------------------------------------------------------------------------
# Page geometry — per-exporter, NOT unified
# ---------------------------------------------------------------------------

PDF_AUTHOR = "SHIELD by Kentro"

SERVICE_PAGE_MARGIN_IN = 0.6
"""Side margin for the four service exporters (tech debt, ATT&CK, CSF, ZT)."""

PLAYBOOK_PAGE_MARGIN_IN = 0.7
"""Side margin for the CSF playbook. Wider on purpose; do not unify."""

PAGE_MARGIN_VERTICAL_IN = 0.7
"""Top/bottom margin. The one value both families already agreed on."""


def new_pdf_doc(out: Any, *, title: str, side_margin_in: float) -> Any:
    """A letter-size reportlab doc template at the caller's side margin."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate

    if side_margin_in <= 0:
        raise ValueError(f"{_LOG} side_margin_in must be positive, got {side_margin_in!r}")
    logger.debug("%s new_pdf_doc side_margin_in=%s title=%r", _LOG, side_margin_in, title)
    return SimpleDocTemplate(
        out,
        pagesize=letter,
        leftMargin=side_margin_in * inch,
        rightMargin=side_margin_in * inch,
        topMargin=PAGE_MARGIN_VERTICAL_IN * inch,
        bottomMargin=PAGE_MARGIN_VERTICAL_IN * inch,
        title=title,
        author=PDF_AUTHOR,
    )


# ---------------------------------------------------------------------------
# XLSX
# ---------------------------------------------------------------------------


def xlsx_header_fill() -> Any:
    """The solid sunken-surface fill every export's header row uses."""
    from openpyxl.styles import PatternFill

    logger.debug("%s xlsx_header_fill %s", _LOG, XLSX_HEADER_ARGB)
    return PatternFill(
        start_color=XLSX_HEADER_ARGB,
        end_color=XLSX_HEADER_ARGB,
        fill_type="solid",
    )
