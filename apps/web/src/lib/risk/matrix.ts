/**
 * Risk 5x5 tier helpers — a faithful client-side mirror of the Python
 * app/risk/engine.py so the dashboard heatmap colours each cell the same way
 * the backend tiers an entry. The backend remains the source of truth; this is
 * presentation only.
 */

export const LIKELIHOODS = [
  "very_low",
  "low",
  "medium",
  "high",
  "very_high",
] as const;
export const IMPACTS = [
  "negligible",
  "minor",
  "moderate",
  "major",
  "catastrophic",
] as const;

export type Likelihood = (typeof LIKELIHOODS)[number];
export type Impact = (typeof IMPACTS)[number];
export type RiskTier = "critical" | "high" | "medium" | "low" | "negligible";

export function riskScore(l: Likelihood, i: Impact): number {
  return (LIKELIHOODS.indexOf(l) + 1) * (IMPACTS.indexOf(i) + 1);
}

export function tierFor(l: Likelihood, i: Impact): RiskTier {
  const ii = IMPACTS.indexOf(i);
  if ((l === "high" || l === "very_high") && i === "catastrophic")
    return "critical";
  if (l === "very_high" && ii >= IMPACTS.indexOf("major")) return "critical";
  const s = riskScore(l, i);
  if (s >= 15) return "high";
  if (s >= 9) return "medium";
  if (s >= 4) return "low";
  return "negligible";
}

/**
 * Tier colours as token references, never literals. The five pairs live in
 * `packages/design-system/src/tokens.css` as `--tier-*-{bg,fg}` and are exposed
 * through the Tailwind preset as `tier.<tier>-{bg,fg}`, so a second theme
 * overrides them in one place. `matrix.test.ts` resolves every entry back
 * through tokens.css and asserts it still equals the hex it replaced.
 */
export const TIER_COLOR: Record<RiskTier, { bg: string; fg: string }> = {
  critical: { bg: "var(--tier-critical-bg)", fg: "var(--tier-critical-fg)" },
  high: { bg: "var(--tier-high-bg)", fg: "var(--tier-high-fg)" },
  medium: { bg: "var(--tier-medium-bg)", fg: "var(--tier-medium-fg)" },
  low: { bg: "var(--tier-low-bg)", fg: "var(--tier-low-fg)" },
  negligible: {
    bg: "var(--tier-negligible-bg)",
    fg: "var(--tier-negligible-fg)",
  },
};

export function titleCase(s: string | null | undefined): string {
  if (!s) return "—";
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function isLikelihood(s: string | null): s is Likelihood {
  return s != null && (LIKELIHOODS as readonly string[]).includes(s);
}

export function isImpact(s: string | null): s is Impact {
  return s != null && (IMPACTS as readonly string[]).includes(s);
}
