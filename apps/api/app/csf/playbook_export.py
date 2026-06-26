"""CSF full-Playbook XLSX export (Work Order D4).

A functional workbook over the data the engine already computes: an Enterprise
Profile sheet (the weighted-floor roll-up per subcategory) plus one sheet per
tier with the five dimension scores and the code-computed total/level/cap. The
methodology doc's exact cell styling can layer on top later; the data + structure
are here.
"""

from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from typing import Any


def _autofit(ws: Any) -> None:
    for col in ws.columns:
        width = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(60, max(10, width + 2))


def render_xlsx(
    *,
    client_name: str,
    version: int,
    enterprise_rows: Sequence[Any],
    tier_profiles: Mapping[str, Sequence[Any]],
) -> bytes:
    """`enterprise_rows` are EnterpriseSubcategory-like; `tier_profiles` maps a
    tier name to its CsfDimensionScoreResponse-like rows (total/level computed)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    head_fill = PatternFill(start_color="FFEEF2F7", end_color="FFEEF2F7", fill_type="solid")

    def _header(ws: Any, cols: list[str]) -> None:
        ws.append(cols)
        for i in range(1, len(cols) + 1):
            cell = ws.cell(row=1, column=i)
            cell.font = Font(bold=True)
            cell.fill = head_fill

    ws = wb.active
    ws.title = "Enterprise Profile"
    _header(
        ws,
        [
            "Subcategory", "Function", "Outcome", "High", "Mod", "Low",
            "Enterprise", "Rule", "Target", "Gap", "Priority",
        ],
    )
    for r in enterprise_rows:
        levels = r.tier_levels
        ws.append(
            [
                r.subcategory_code,
                r.function,
                r.name,
                levels.get("high", ""),
                levels.get("moderate", ""),
                levels.get("low", ""),
                f"L{r.enterprise_level}",
                f"#{r.rollup_rule}",
                f"L{r.target_level}" if r.target_level else "",
                "Yes" if r.gap else "",
                r.priority or "",
            ]
        )
    _autofit(ws)

    for tier in ("high", "moderate", "low"):
        rows = tier_profiles.get(tier)
        if not rows:
            continue
        ts = wb.create_sheet(tier.title())
        _header(
            ts,
            [
                "Subcategory", "Governance", "Policy & Process", "Implementation",
                "Monitoring & Measurement", "Continuous Improvement", "Total",
                "Level", "Evidence capped", "In scope", "Target",
            ],
        )
        for row in rows:
            ts.append(
                [
                    row.subcategory_code,
                    row.governance,
                    row.policy,
                    row.implementation,
                    row.monitoring,
                    row.improvement,
                    row.total,
                    f"L{row.level}",
                    "Yes" if row.evidence_capped else "",
                    "Yes" if row.in_scope else "No",
                    f"L{row.target_level}" if row.target_level else "",
                ]
            )
        _autofit(ts)

    # A small cover note so the export is self-describing.
    cover = wb.create_sheet("About", 0)
    cover.append(["SHIELD by Kentro — CSF 2.0 Full Playbook"])
    cover.append([f"Client: {client_name}"])
    cover.append([f"Working profile version: {version}"])
    cover.append([])
    cover.append([
        "Levels are code-computed: total = sum of the five dimensions (0-10); "
        "L1 0-2, L2 3-5, L3 6-7, L4 8-9, L5 10. Enterprise = weighted-floor "
        "roll-up across the tiers in use."
    ])
    cover["A1"].font = Font(bold=True, size=14)

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
