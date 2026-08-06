# S0 evidence — served-CSS proof that the refactor is colourless

Captured 2026-08-03T21:19:09Z by the loop driver, independently of the
runner's vitest, by fetching the compiled stylesheet the browser actually receives
from the running web container (host port 3001).

## The ten tier values as served

```
--tier-critical-bg: #fee2e2
--tier-critical-fg: #991b1b
--tier-high-bg: #ffedd5
--tier-high-fg: #9a3412
--tier-low-bg: #dcfce7
--tier-low-fg: #166534
--tier-medium-bg: #fef9c3
--tier-medium-fg: #854d0e
--tier-negligible-bg: #f1f5f9
--tier-negligible-fg: #475569
```

## The same ten values before S0, from git

```
$ git show main:apps/web/src/lib/risk/matrix.ts
export const TIER_COLOR: Record<RiskTier, { bg: string; fg: string }> = {
  critical: { bg: "#fee2e2", fg: "#991b1b" },
  high: { bg: "#ffedd5", fg: "#9a3412" },
  medium: { bg: "#fef9c3", fg: "#854d0e" },
  low: { bg: "#dcfce7", fg: "#166534" },
  negligible: { bg: "#f1f5f9", fg: "#475569" },
};
```

Every pair is identical, keyed by tier name. Note the trap avoided: the S0
acceptance criterion in docs/SPRINTS.md lists the token names in the order
negligible,low,medium,high,critical but lists the hexes starting with critical's
pair, so a positional reading would have inverted the whole ramp.

## Cell separation as served

```
border-spacing: var(--tw-border-spacing-x) var(--tw-border-spacing-y)
border-separate present: 1 rule(s)
```
