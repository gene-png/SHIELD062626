"""Zero Trust maturity scales.

CISA ZTMM 2.0 uses a four-stage model; the DoD ZT Reference Architecture
adds a "Pre Zero Trust" baseline below its first stage:

CISA:                 Traditional (1) -> Initial (2) -> Advanced (3) -> Optimal (4)
DoD: Pre Zero Trust (0) -> Baseline (1) -> Target  (2) -> Advanced (3) -> Optimal (4)

For storage + scoring we use a single integer scale and label the stage by
framework at render time. Stage 0 ("Pre Zero Trust") is DoD-only — CISA's
scale starts at 1. `stage_definitions()` returns the framework-appropriate
ladder so the catalog only ever offers stages that exist for that framework.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ZtFrameworkCode(enum.StrEnum):
    CISA_ZTMM_2_0 = "cisa_ztmm_2_0"
    DOD_ZTRA = "dod_ztra"


class MaturityStage(enum.IntEnum):
    # DoD-only baseline below "Baseline" — no formal ZT adopted yet.
    STAGE_0 = 0
    STAGE_1 = 1
    STAGE_2 = 2
    STAGE_3 = 3
    STAGE_4 = 4


@dataclass(frozen=True)
class StageDefinition:
    stage: MaturityStage
    cisa_label: str
    dod_label: str
    description: str


# DoD "Pre Zero Trust" baseline (stage 0). CISA has no equivalent, so this
# definition is only ever surfaced for the DoD framework; `cisa_label` exists
# only to satisfy the dataclass shape and is never read for CISA.
DOD_PRE_ZERO_TRUST = StageDefinition(
    stage=MaturityStage.STAGE_0,
    cisa_label="Pre Zero Trust",
    dod_label="Pre Zero Trust",
    description=(
        "Foundational hygiene only — perimeter-based access and no formal "
        "Zero Trust strategy adopted yet."
    ),
)


STAGE_DEFINITIONS: tuple[StageDefinition, ...] = (
    StageDefinition(
        stage=MaturityStage.STAGE_1,
        cisa_label="Traditional",
        dod_label="Baseline",
        description=(
            "Manual, perimeter-centric controls. Limited automation; static "
            "trust decisions."
        ),
    ),
    StageDefinition(
        stage=MaturityStage.STAGE_2,
        cisa_label="Initial",
        dod_label="Target",
        description=(
            "Starting Zero Trust adoption. Inventory and identity verified "
            "but trust is still mostly implicit after auth."
        ),
    ),
    StageDefinition(
        stage=MaturityStage.STAGE_3,
        cisa_label="Advanced",
        dod_label="Advanced",
        description=(
            "Cross-pillar coordination; risk-adaptive access decisions; "
            "automated response to a defined set of conditions."
        ),
    ),
    StageDefinition(
        stage=MaturityStage.STAGE_4,
        cisa_label="Optimal",
        dod_label="Optimal",
        description=(
            "Fully automated, continuously evaluated trust. Just-in-time "
            "access. Self-healing controls informed by analytics."
        ),
    ),
)


def stage_definitions(framework: ZtFrameworkCode) -> tuple[StageDefinition, ...]:
    """Framework-appropriate maturity ladder.

    DoD prepends the "Pre Zero Trust" baseline (stage 0); CISA starts at 1.
    """
    if framework == ZtFrameworkCode.DOD_ZTRA:
        return (DOD_PRE_ZERO_TRUST, *STAGE_DEFINITIONS)
    return STAGE_DEFINITIONS


def stage_label(stage: MaturityStage | int | None, framework: ZtFrameworkCode) -> str:
    if stage is None:
        return "Unscored"
    value = int(stage)
    for d in stage_definitions(framework):
        if int(d.stage) == value:
            return d.cisa_label if framework == ZtFrameworkCode.CISA_ZTMM_2_0 else d.dod_label
    return "Unknown"
