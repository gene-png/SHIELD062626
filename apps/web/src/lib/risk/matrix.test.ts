import { readFileSync } from "node:fs";
// Node's own URL, not the global one: the jsdom environment replaces global
// URL with jsdom's implementation, and fileURLToPath rejects the object it
// returns ("The URL must be of scheme file").
import { fileURLToPath, URL as NodeUrl } from "node:url";

import { describe, expect, it } from "vitest";

import { TIER_COLOR, type RiskTier } from "./matrix";

/**
 * S0 colourless-refactor guard.
 *
 * The five risk tiers used to be hard-coded hexes in `matrix.ts`, invisible to
 * theming. They now live in `tokens.css` as `--tier-*` custom properties, which
 * a second theme can override. These cases resolve every TIER_COLOR entry
 * through tokens.css and assert it still equals the literal it replaced, so the
 * move is provably colourless: change any of the ten values and this file goes
 * red.
 */

/**
 * Both design-system files are read as text, not imported. `tailwind-preset.ts`
 * imports its Config type from `tailwindcss`, which pnpm installs only in
 * apps/web/node_modules — importing the preset from here drags it into the web
 * app's TS program, where that specifier cannot resolve and `tsc --noEmit`
 * fails. Paths resolve from this file, not from cwd, so the suite does not care
 * whether it was launched from apps/web or the repo root.
 */
function designSystemSource(file: string): string {
  const path = fileURLToPath(
    new NodeUrl(
      `../../../../../packages/design-system/src/${file}`,
      import.meta.url,
    ),
  );
  return readFileSync(path, "utf8");
}

const TOKENS_CSS_PATH = "packages/design-system/src/tokens.css";
const TOKENS_CSS = designSystemSource("tokens.css");
const TAILWIND_PRESET = designSystemSource("tailwind-preset.ts");

/** The declared value of a custom property in tokens.css. Throws if absent. */
function declaredToken(name: string): string {
  const match = new RegExp(`(?:^|\\s)${name}:\\s*([^;]+);`).exec(TOKENS_CSS);
  if (!match) {
    throw new Error(`${name} is not declared in ${TOKENS_CSS_PATH}`);
  }
  return match[1].trim();
}

/** Resolve a `var(--token)` reference to the literal tokens.css gives it. */
function resolveCssValue(value: string): string {
  const match = /^var\((--[a-z0-9-]+)\)$/.exec(value);
  if (!match) {
    throw new Error(`expected a var() token reference, got "${value}"`);
  }
  return declaredToken(match[1]);
}

/**
 * The exact literals TIER_COLOR carried before S0. Frozen on purpose — this is
 * the "before" side of the equality, so it must never be edited to match the
 * code.
 */
const FROZEN_TIER_HEX: Record<RiskTier, { bg: string; fg: string }> = {
  critical: { bg: "#fee2e2", fg: "#991b1b" },
  high: { bg: "#ffedd5", fg: "#9a3412" },
  medium: { bg: "#fef9c3", fg: "#854d0e" },
  low: { bg: "#dcfce7", fg: "#166534" },
  negligible: { bg: "#f1f5f9", fg: "#475569" },
};

const TIERS = Object.keys(FROZEN_TIER_HEX) as RiskTier[];

describe("TIER_COLOR is tokenised without changing a single value", () => {
  it.each(TIERS)(
    "%s resolves through tokens.css to the exact hexes it replaced",
    (tier) => {
      expect(resolveCssValue(TIER_COLOR[tier].bg)).toBe(
        FROZEN_TIER_HEX[tier].bg,
      );
      expect(resolveCssValue(TIER_COLOR[tier].fg)).toBe(
        FROZEN_TIER_HEX[tier].fg,
      );
    },
  );

  it("names a --tier-* token instead of inlining a hex", () => {
    for (const tier of TIERS) {
      expect(TIER_COLOR[tier].bg).toBe(`var(--tier-${tier}-bg)`);
      expect(TIER_COLOR[tier].fg).toBe(`var(--tier-${tier}-fg)`);
    }
  });

  it("exposes all ten tier tokens through the Tailwind preset", () => {
    for (const t of TIERS) {
      expect(TAILWIND_PRESET).toContain(`"${t}-bg": "var(--tier-${t}-bg)"`);
      expect(TAILWIND_PRESET).toContain(`"${t}-fg": "var(--tier-${t}-fg)"`);
    }
  });
});
