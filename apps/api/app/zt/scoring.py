"""Zero Trust scoring + gap engine.

Pure functions. Given a `capability_code -> maturity_stage` map for a
chosen framework, produces:
  - Overall maturity stage (band-cutoff label)
  - Per-pillar stage rollup with coverage + weakest codes
  - Top-N prioritized gaps against a target stage

Framework awareness: the labels (Traditional/Initial/... for CISA,
Baseline/Target/... for DoD) are picked from the maturity module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.zt.catalog import (
    Capability,
    capabilities,
    pillars,
)
from app.zt.maturity import (
    MaturityStage,
    ZtFrameworkCode,
    stage_label,
)

WEAKEST_PER_PILLAR = 5
DEFAULT_TARGET_STAGE = int(MaturityStage.STAGE_3)
DEFAULT_TOP_N = 20

# Pillar weights for gap prioritization. Identity + Data score highest
# in the typical FedRAMP / DoD risk picture because they sit closest to
# the protected resources; supporting pillars carry a 1.0 baseline.
_PILLAR_WEIGHTS: dict[str, float] = {
    # CISA codes
    "ID": 1.20,  # Identity
    "DT": 1.15,  # Data
    "DV": 1.10,  # Devices
    "NW": 1.05,  # Networks
    "AW": 1.10,  # Applications & Workloads
    "VA": 1.00,  # Visibility & Analytics (cross-cutting)
    "AO": 1.00,  # Automation & Orchestration (cross-cutting)
    "GV": 1.00,  # Governance (cross-cutting)
    # DoD codes
    "USR": 1.20,
    "DAT": 1.15,
    "DEV": 1.10,
    "NET": 1.05,
    "APP": 1.10,
    "VIS": 1.00,
    "AUT": 1.00,
}


@dataclass(frozen=True)
class PillarScoreResult:
    pillar_code: str
    pillar_name: str
    capability_count: int
    answered_count: int
    average_stage: float | None
    coverage_pct: float
    weakest_capability_codes: tuple[str, ...]


@dataclass(frozen=True)
class ScoreResult:
    framework: ZtFrameworkCode
    total_capabilities: int
    answered_capabilities: int
    coverage_pct: float
    average_stage: float | None
    overall_stage_label: str
    by_pillar: tuple[PillarScoreResult, ...]


@dataclass(frozen=True)
class Gap:
    code: str
    pillar_code: str
    pillar_name: str
    name: str
    outcome: str
    current_stage: int
    target_stage: int
    gap_size: int
    priority_score: float
    notes: str | None


@dataclass(frozen=True)
class GapAnalysis:
    framework: ZtFrameworkCode
    target_stage: int
    target_label: str
    gaps: tuple[Gap, ...]
    unscored_codes: tuple[str, ...]
    total_gap_count: int
    gap_count_by_pillar: dict[str, int]


def _coverage_pct(answered: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(answered / total * 100, 1)


def _round_average(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _validated(stage: int | None) -> int | None:
    if stage is None:
        return None
    # Stage 0 ("Pre Zero Trust") is a valid DoD floor; CISA never emits it.
    if 0 <= int(stage) <= 4:
        return int(stage)
    return None


def _label_from_average(avg: float | None, framework: ZtFrameworkCode) -> str:
    if avg is None:
        return "Unscored"
    if avg < 0.5:
        return stage_label(MaturityStage.STAGE_0, framework)
    if avg < 1.5:
        return stage_label(MaturityStage.STAGE_1, framework)
    if avg < 2.5:
        return stage_label(MaturityStage.STAGE_2, framework)
    if avg < 3.5:
        return stage_label(MaturityStage.STAGE_3, framework)
    return stage_label(MaturityStage.STAGE_4, framework)


def _pillar_name_lookup(framework: ZtFrameworkCode) -> dict[str, str]:
    return {p.code: p.name for p in pillars(framework)}


def compute(
    framework: ZtFrameworkCode, answers: Mapping[str, int | None]
) -> ScoreResult:
    names = _pillar_name_lookup(framework)
    pillar_results: list[PillarScoreResult] = []
    overall_values: list[int] = []
    total = 0
    answered = 0

    for p in pillars(framework):
        codes = [c.code for c in capabilities(framework) if c.pillar_code == p.code]
        pillar_total = len(codes)
        total += pillar_total

        scored_pairs: list[tuple[str, int]] = []
        for code in codes:
            s = _validated(answers.get(code))
            if s is not None:
                scored_pairs.append((code, s))

        answered += len(scored_pairs)
        overall_values.extend(s for _, s in scored_pairs)

        scored_pairs.sort(key=lambda p: (p[1], p[0]))
        weakest = tuple(code for code, _ in scored_pairs[:WEAKEST_PER_PILLAR])

        pillar_results.append(
            PillarScoreResult(
                pillar_code=p.code,
                pillar_name=names.get(p.code, p.code),
                capability_count=pillar_total,
                answered_count=len(scored_pairs),
                average_stage=_round_average([s for _, s in scored_pairs]),
                coverage_pct=_coverage_pct(len(scored_pairs), pillar_total),
                weakest_capability_codes=weakest,
            )
        )

    avg_overall = _round_average(overall_values)
    return ScoreResult(
        framework=framework,
        total_capabilities=total,
        answered_capabilities=answered,
        coverage_pct=_coverage_pct(answered, total),
        average_stage=avg_overall,
        overall_stage_label=_label_from_average(avg_overall, framework),
        by_pillar=tuple(pillar_results),
    )


def _row_for(
    cap: Capability,
    current: int,
    target: int,
    notes: str | None,
    pillar_name: str,
) -> Gap:
    gap_size = max(0, target - current)
    weight = _PILLAR_WEIGHTS.get(cap.pillar_code, 1.0)
    priority = round(gap_size * weight, 2)
    return Gap(
        code=cap.code,
        pillar_code=cap.pillar_code,
        pillar_name=pillar_name,
        name=cap.name,
        outcome=cap.outcome,
        current_stage=current,
        target_stage=target,
        gap_size=gap_size,
        priority_score=priority,
        notes=notes,
    )


def analyze_gaps(
    framework: ZtFrameworkCode,
    answers: Mapping[str, int | None],
    *,
    notes: Mapping[str, str | None] | None = None,
    target_stage: int = DEFAULT_TARGET_STAGE,
    top_n: int = DEFAULT_TOP_N,
) -> GapAnalysis:
    if not (1 <= target_stage <= 4):
        target_stage = DEFAULT_TARGET_STAGE
    notes = notes or {}
    names = _pillar_name_lookup(framework)

    rows: list[Gap] = []
    unscored: list[str] = []
    for cap in capabilities(framework):
        s = _validated(answers.get(cap.code))
        if s is None:
            unscored.append(cap.code)
            continue
        if s >= target_stage:
            continue
        pillar_name = names.get(cap.pillar_code, cap.pillar_code)
        rows.append(
            _row_for(cap, s, target_stage, notes.get(cap.code), pillar_name)
        )

    rows.sort(key=lambda g: (-g.priority_score, g.code))

    by_pillar: dict[str, int] = {}
    for g in rows:
        by_pillar[g.pillar_code] = by_pillar.get(g.pillar_code, 0) + 1

    return GapAnalysis(
        framework=framework,
        target_stage=target_stage,
        target_label=stage_label(target_stage, framework),
        gaps=tuple(rows[:top_n]),
        unscored_codes=tuple(unscored),
        total_gap_count=len(rows),
        gap_count_by_pillar=by_pillar,
    )


__all__ = [
    "DEFAULT_TARGET_STAGE",
    "DEFAULT_TOP_N",
    "Gap",
    "GapAnalysis",
    "PillarScoreResult",
    "ScoreResult",
    "WEAKEST_PER_PILLAR",
    "analyze_gaps",
    "compute",
]
