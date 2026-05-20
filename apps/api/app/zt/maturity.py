"""Zero Trust maturity scales.

Both CISA ZTMM 2.0 and the DoD ZT Reference Architecture use four-stage
models with slightly different vocabulary:

CISA: Traditional (1) -> Initial (2) -> Advanced (3) -> Optimal (4)
DoD:  Baseline    (1) -> Target  (2) -> Advanced (3) -> Optimal (4)

For storage + scoring we use a single integer scale 1-4 and label the
stage by framework at render time. This keeps the scoring engine
framework-agnostic.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ZtFrameworkCode(enum.StrEnum):
    CISA_ZTMM_2_0 = "cisa_ztmm_2_0"
    DOD_ZTRA = "dod_ztra"


class MaturityStage(enum.IntEnum):
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


def stage_label(stage: MaturityStage | int | None, framework: ZtFrameworkCode) -> str:
    if stage is None:
        return "Unscored"
    value = int(stage)
    for d in STAGE_DEFINITIONS:
        if int(d.stage) == value:
            return d.cisa_label if framework == ZtFrameworkCode.CISA_ZTMM_2_0 else d.dod_label
    return "Unknown"
