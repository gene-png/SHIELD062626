# Three visual systems for SHIELD

_Produced 2026-07-30 in a design sprint. **Status: Variation 1 "Ledger" was chosen on
2026-08-06.** The decision is recorded in `ROADMAP.md`; its D-number lands in the sprint
that applies it, which is where `DECISIONS.md` gets the entry. Cloud Mod
(`kentro-cloud-modernization`) is retrofitted onto the same tokens in the sprint after,
retiring `kentro.teal` as a second brand ramp._

_Re-run the contrast evidence with `node docs/design-systems-contrast.mjs` from the repo
root. It exits non-zero on any failure, so it can become a CI step when a system is
adopted._

Three complete visual systems for the existing app: same routes, same components, same hierarchy, different argument about what the product is. Every color pairing claimed below was computed with a WCAG 2.1 relative-luminance checker (`docs/design-systems-contrast.mjs`), 234 pairings total, zero failures. Ratios quoted are from that run, not estimated.

## What grounding in the code turned up

Facts that shape all three proposals, found by reading the app rather than the brief:

1. **The heatmap ramp is off-contract today.** `apps/web/src/lib/risk/matrix.ts` lines 43 to 49 hard-code `TIER_COLOR` hexes (Tailwind's red-100/orange-100/yellow-100/green-100/slate-100 family) applied via inline `style`, invisible to any theme. The 5x5 matrix in `RiskRegisterDashboard.tsx` separates cells with `border border-white` (line 90), which will glow in any dark mode. Both must move onto tokens before a second theme can exist. All three variations therefore share a new token family (below).
2. **Inter never actually loads.** The token stack names Inter first, but there is no `next/font` usage and no `@font-face` anywhere in `apps/web`. On the Windows dev boxes the app renders Segoe UI today. Any variation that names a family must ship it with `next/font/local` (woff2 in the repo, zero runtime egress), and every stack below is written so the self-hosted file is the first name and the rest is OS-safe.
3. **Exporters carry their own palette.** `apps/api/app/risk/exporters.py` line 123 fills XLSX headers with `FFEEF2F7`, the current `--surface-sunken`. Six exporter modules use `PatternFill`/`RGBColor`. Adopting any variation means mirroring its light-mode ramp and surface values into those constants, or the app and the deliverable stop matching, which is exactly the credibility failure the product cannot afford.
4. **A latent no-op, wider than it first looked:** `bg-surface-muted` and `hover:bg-surface-muted` appear 8 times across 6 files (`AiPreviewButton.tsx` twice, `CsfPlaybookPanel.tsx`, `DiscardDraftButton.tsx`, `RiskRegisterDashboard.tsx` twice, `KeycloakSignInButton.tsx`, `MfaEnrollment.tsx`). No `surface-muted` token or Tailwind color exists, so every one of them silently emits nothing and no build step complains. Fix to `bg-surface-sunken` regardless of which variation wins. Scoped by grep on 2026-07-30; see S0 in `docs/SPRINTS.md`.
5. **Class-pair semantics that dark mode must preserve.** The codebase pairs `bg-brand-500 text-ink-on-accent hover:bg-brand-600` for filled buttons, `bg-brand-50 text-brand-600` for selected nav and chips, and uses `text-brand-500`/`text-brand-600` as link text on cards. So in dark mode the brand ramp must invert: 50 becomes the darkest tint, 700 the lightest text, and `--ink-on-accent` flips to near-black because brand-500 must be light enough to read as text on a dark card. All three dark palettes below obey this, and every one of those pairs was checked in both modes.

## Shared mechanics (all three variations)

**Dark mode plumbing.** One `:root[data-theme="dark"]` block per variation, toggled by a `data-theme` attribute on `<html>` plus `color-scheme: dark`. `globals.css` line 18 currently pins `color-scheme: light`; it becomes theme-aware. The `s16-axe` runtime sweep runs twice, once per mode, and the dark run is a gate, not a courtesy.

**New tokens, named and justified.**

- `--heat-1` through `--heat-5` and `--heat-ink-1` through `--heat-ink-5`: the sequential ramp for coverage heatmaps and the ink guaranteed AA on each step. Justified by fact 1 above; today this data has no tokens at all.
- `--tier-negligible-bg/-fg`, `--tier-low-bg/-fg`, `--tier-medium-bg/-fg`, `--tier-high-bg/-fg`, `--tier-critical-bg/-fg`: the ten values `TIER_COLOR` currently hard-codes. The risk engine's five tiers are a fixed product concept; they deserve first-class tokens because they appear in the app and in every exported register.
- Variation 1 additionally adds `--font-serif` (it is the only one that needs a second family for headings).

**Heatmap discipline (from the dataviz review).** Sequential ramps are one hue, light to dark, five steps. Cells get a 2px gap in the surface color (replacing `border-white`). Cell values print in every occupied cell, in the step's paired ink, so the number survives grayscale printing and colorblind viewing. The risk 5x5 uses the tier tokens, which are status colors, not a rainbow.

---

# Variation 1: Ledger

**Design thesis.** The app is the instrument of record for an audit, and it should look like the document it produces. Warm paper surfaces, hairline rules instead of shadows, square corners, serif headings over a working sans, tabular numerals, status rendered as printed tags rather than glowing pills. Nothing floats; everything is ruled and filed. It flatters the skeptical client executive who will read the exported PDF with a red pen, because the screen and the deliverable share one typographic voice. Dark mode is a reading room, warm charcoal rather than blue-black, built for consultants doing long evening review passes.

## Tokens: light

```css
:root {
  /* ----- Surface ----- */
  --surface-canvas: #f7f5f0;
  --surface-card: #fffdf8;
  --surface-raised: #fffdf8;
  --surface-sunken: #efece3;
  --surface-overlay: rgba(28, 24, 16, 0.55);

  /* ----- Ink ----- */
  --ink-primary: #211d14;
  --ink-secondary: #4c473b;
  --ink-tertiary: #6b6557; /* 4.91:1 on sunken, 5.70:1 on card */
  --ink-on-accent: #fffdf8;
  --ink-disabled: #a9a292;

  /* ----- Border (hairlines carry the whole surface model) ----- */
  --border-subtle: #e7e2d4;
  --border-default: #d5cfbe;
  --border-strong: #857e6b; /* 3.98:1 on card, clears 3:1 non-text */
  --border-focus: #2b5c44;

  /* ----- Brand (ledger green) ----- */
  --brand-50: #edf1ea;
  --brand-100: #d7e2d2;
  --brand-300: #7f9d84;
  --brand-500: #2b5c44; /* 7.60:1 as text on card; white on it 7.60:1 */
  --brand-600: #204832;
  --brand-700: #173425;

  /* ----- Status (printed-tag palette) ----- */
  --status-success-bg: #e9f1e7;
  --status-success-fg: #2c633f; /* 6.14:1 on bg */
  --status-success-border: #a6c4a4;
  --status-warning-bg: #f7edd2;
  --status-warning-fg: #7d5a0e; /* 5.39:1 on bg */
  --status-warning-border: #d8bc78;
  --status-danger-bg: #f6e3dd;
  --status-danger-fg: #99311f; /* 6.02:1 on bg */
  --status-danger-border: #dba290;
  --status-info-bg: #e6ecf3;
  --status-info-fg: #31567a; /* 6.44:1 on bg */
  --status-info-border: #a9bdd2;
  --status-neutral-bg: #edeade;
  --status-neutral-fg: #5a5545; /* 6.18:1 on bg */
  --status-neutral-border: #c8c1ab;

  /* ----- Heat (sequential, single green hue) ----- */
  --heat-1: #eaf0e6;
  --heat-ink-1: #211d14; /* 14.48:1 */
  --heat-2: #c9dac2;
  --heat-ink-2: #211d14; /* 11.43:1 */
  --heat-3: #a3c19d;
  --heat-ink-3: #211d14; /*  8.53:1 */
  --heat-4: #6f9d74;
  --heat-ink-4: #211d14; /*  5.40:1 */
  --heat-5: #35664b;
  --heat-ink-5: #fffdf8; /*  6.55:1 */

  /* ----- Risk tiers ----- */
  --tier-negligible-bg: #eeebe0;
  --tier-negligible-fg: #5a5545; /* 6.24:1 */
  --tier-low-bg: #dfe9d5;
  --tier-low-fg: #3e5c2a; /* 6.05:1 */
  --tier-medium-bg: #f1e3b3;
  --tier-medium-fg: #6c5410; /* 5.62:1 */
  --tier-high-bg: #f0cba2;
  --tier-high-fg: #7d3f10; /* 5.32:1 */
  --tier-critical-bg: #e9b0a5;
  --tier-critical-fg: #85271a; /* 4.87:1 */

  /* ----- Type ----- */
  --font-sans:
    "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI",
    "Helvetica Neue", Arial, sans-serif;
  --font-serif:
    "Source Serif 4", Georgia, "Times New Roman", serif; /* NEW token */
  --font-mono:
    ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", Menlo, Consolas,
    monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  --text-display: 3.25rem;

  --leading-tight: 1.2;
  --leading-snug: 1.35;
  --leading-normal: 1.55;
  --leading-relaxed: 1.7;

  /* ----- Spacing (unchanged 4-px grid) ----- */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* ----- Radii (print geometry) ----- */
  --radius-xs: 0px;
  --radius-sm: 2px;
  --radius-md: 2px;
  --radius-lg: 3px;
  --radius-xl: 4px;
  --radius-pill: 2px; /* pills become tags on purpose */

  /* ----- Shadows (rules, not lift) ----- */
  --shadow-sm: none;
  --shadow-md: 0 0 0 1px #d5cfbe;
  --shadow-lg: 0 16px 32px -16px rgba(33, 29, 20, 0.2), 0 0 0 1px #d5cfbe;

  /* ----- Motion ----- */
  --motion-duration-fast: 120ms;
  --motion-duration: 180ms;
  --motion-ease: cubic-bezier(0.2, 0.7, 0.2, 1);

  /* ----- Z layers ----- */
  --z-base: 0;
  --z-overlay: 50;
  --z-toast: 80;
  --z-modal: 100;
}
```

## Tokens: dark

Dark overrides color-bearing tokens and shadows only; type, spacing, radii, and motion inherit.

```css
:root[data-theme="dark"] {
  --surface-canvas: #17140e;
  --surface-card: #201c14;
  --surface-raised: #272218;
  --surface-sunken: #100d09;
  --surface-overlay: rgba(0, 0, 0, 0.65);

  --ink-primary: #ece5d4;
  --ink-secondary: #c3bba6;
  --ink-tertiary: #a09781; /* 5.85:1 on card, 5.45:1 on raised */
  --ink-on-accent: #171310; /* flips dark: brand fills are light here */
  --ink-disabled: #5f584a;

  --border-subtle: #363023;
  --border-default: #453e2e;
  --border-strong: #83795f; /* 3.93:1 on card */
  --border-focus: #7fb08d;

  /* Brand ramp inverts: 50 darkest tint, 700 lightest text */
  --brand-50: #232e24;
  --brand-100: #2b3b2d;
  --brand-300: #5f8a6b;
  --brand-500: #7fb08d; /* 6.87:1 as text on card; on-accent on it 7.47:1 */
  --brand-600: #9cc4a6; /* 7.30:1 on brand-50 */
  --brand-700: #bcd8c2;

  --status-success-bg: #1d2b1e;
  --status-success-fg: #9ac79c; /* 7.78:1 */
  --status-success-border: #3f5c41;
  --status-warning-bg: #2e2611;
  --status-warning-fg: #d5b264; /* 7.41:1 */
  --status-warning-border: #5f4e20;
  --status-danger-bg: #331b14;
  --status-danger-fg: #e39a83; /* 7.05:1 */
  --status-danger-border: #64382a;
  --status-info-bg: #1b2530;
  --status-info-fg: #9db9d6; /* 7.64:1 */
  --status-info-border: #3c5064;
  --status-neutral-bg: #262215;
  --status-neutral-fg: #b5ac93; /* 7.02:1 */
  --status-neutral-border: #4a4330;

  --heat-1: #20281f;
  --heat-ink-1: #ece5d4; /* 12.08:1 */
  --heat-2: #2b3d2c;
  --heat-ink-2: #ece5d4; /*  9.26:1 */
  --heat-3: #33503a;
  --heat-ink-3: #ece5d4; /*  7.12:1 */
  --heat-4: #47694c;
  --heat-ink-4: #ece5d4; /*  4.93:1 */
  --heat-5: #74ab7e;
  --heat-ink-5: #171310; /*  6.92:1 */

  --tier-negligible-bg: #262215;
  --tier-negligible-fg: #b5ac93; /* 7.02:1 */
  --tier-low-bg: #223320;
  --tier-low-fg: #a9d09e; /* 7.81:1 */
  --tier-medium-bg: #393112;
  --tier-medium-fg: #d9bd57; /* 7.01:1 */
  --tier-high-bg: #402813;
  --tier-high-fg: #e2a263; /* 6.26:1 */
  --tier-critical-bg: #44201a;
  --tier-critical-fg: #ee9f86; /* 6.77:1 */

  --shadow-sm: none;
  --shadow-md: 0 0 0 1px #453e2e;
  --shadow-lg: 0 16px 32px -16px rgba(0, 0, 0, 0.5), 0 0 0 1px #453e2e;
}
```

What changes conceptually in dark: elevation stays flat because Ledger never had lift to begin with; the hairline model translates directly, with rules lightening instead of surfaces shadowing. Status moves from tinted-paper tags to dark-tinted plates with light saturated text, and the tier ramp swaps from "dark ink on light paper" to "warm light ink on dark plates" while keeping identical hue assignments, so a consultant switching modes never relearns the encoding. The heat ramp reverses reading direction (darkest cell = lowest value in dark mode) so the brightest cell is always the one demanding attention.

## Type system

- **Headings** (`h1` to `h3`, `CardTitle`, workspace section heads): `var(--font-serif)`, Source Serif 4, self-hosted woff2 at weights 600 and 400 italic; fallback Georgia, then Times New Roman. Serif at 600 reads as authority without boldface shouting.
- **Body, tables, forms, nav**: the existing Inter stack, now actually self-hosted (400, 500, 600). Dense data never sets in serif.
- **Numerals**: `font-variant-numeric: tabular-nums lining-nums` on every table and score readout, one base-layer rule. Scores that line up vertically are half the credibility argument.
- **Scale**: sizes unchanged except `--text-display` up to 3.25rem for report cover pages; `--leading-normal` 1.55 and `--leading-relaxed` 1.7 buy the editorial air the serif needs. Pairing rationale: one voice for claims (serif), one for evidence (sans), the same split a typeset assessment report already uses.

## Component treatment

- **Data tables**: horizontal rules only; kill the vertical `border-r` in `AttackMatrix` and never add zebra. Header row loses the sunken fill and sits on card with an 11px, 0.08em-tracked uppercase label in `--ink-secondary` and a 1px `--border-strong` bottom rule. Row height 44px. Numeric columns right-aligned tabular. Row hover is `--surface-sunken`, nothing more.
- **Questionnaire question card**: remove the card shell; questions sit directly on canvas, separated by `--space-8` and a `--border-subtle` rule. Prompt in serif at `--text-lg`. The score chips (`QuestionField` score_0_2, yes_no, tristate) become square 2px-radius boxes; selected state is a 2px inset `--brand-500` border plus `--brand-50` fill, unselected is a 1px `--border-default` box.
- **Status pills**: `--radius-pill: 2px` turns every `StatusPill` into a printed tag automatically; the dot becomes a small square tick. Keep the tinted bg and 1px ring; the ring border colors above are darker than today's so the tag reads at print resolution.
- **Heatmap cells**: ruled grid, 1px `--border-default` between cells, no gaps, square corners; every occupied cell prints its count in the paired heat ink. Empty cells stay paper.
- **Workspace stepper** (`IntakeProgress`, `SectionTabs`, `PillarNavigation`): a ruled index list. Steps read "1. Services" with the numeral in serif; current step gets a 2px `--brand-500` underline, completed steps a `--brand-500` check glyph, upcoming steps `--ink-tertiary`. The filled circles go away, which also retires the `bg-ink-disabled` white-on-gray numeral.
- **Cards/panels**: flat, 1px `--border-default`, no shadow (`--shadow-sm: none` does this without touching `Card.tsx`). `CardHeader` keeps its hairline; `CardTitle` picks up serif via the h3 base rule.
- **Buttons**: 2px radius. Primary = `--brand-500` fill, on-accent text. Secondary = 1px `--border-strong` outline, `--ink-primary` text. Tertiary actions become underlined text links.
- **Form inputs**: card-colored field, 1px `--border-default`, 2px radius, 40px height; focus is the existing 2px outline in `--border-focus`. Labels 13px at weight 600.

## Heatmap ramp (summary table)

| Step        | Light fill | Light ink | Ratio | Dark fill | Dark ink | Ratio |
| ----------- | ---------- | --------- | ----- | --------- | -------- | ----- |
| 1 (0-20%)   | #eaf0e6    | #211d14   | 14.48 | #20281f   | #ece5d4  | 12.08 |
| 2           | #c9dac2    | #211d14   | 11.43 | #2b3d2c   | #ece5d4  | 9.26  |
| 3           | #a3c19d    | #211d14   | 8.53  | #33503a   | #ece5d4  | 7.12  |
| 4           | #6f9d74    | #211d14   | 5.40  | #47694c   | #ece5d4  | 4.93  |
| 5 (80-100%) | #35664b    | #fffdf8   | 6.55  | #74ab7e   | #171310  | 6.92  |

Risk tiers use the `--tier-*` pairs listed in the token blocks; the light-mode critical pairing (#85271a on #e9b0a5) is the tightest at 4.87:1 and still clears AA. The ramp is monotonic in lightness, so it survives grayscale printing, which matters because the XLSX and PDF exports will be photocopied.

## What it costs

- `--radius-pill: 2px` reshapes every `rounded-pill` element (StatusPill, stepper numerals, ClientSwitcher, dots). That is the intent, but it needs a visual QA pass over roughly ten components.
- Serif adoption is one base-layer rule for h1-h3 plus self-hosting two Source Serif 4 weights; `CardTitle` is already an `h3` so the design system package needs no API change.
- `DataTable.tsx` needs the header-fill removal and a `tabular-nums` class; `AttackMatrix.tsx` loses its `border-r`.
- The warm palette means auditing for hard-coded cool values: `border-white` in the risk matrix (shared fix), and any raw `#fff` in components.
- Exporter mirroring: `FFEEF2F7` header fills become `FFEFECE3`, and the tier/heat hexes above go into `risk/exporters.py` and the ATT&CK exporter constants.
- Axe risk: low. All 39 light and 39 dark pairings verified; the closest light-mode call is tertiary ink on sunken at 4.91:1, comfortably above the current contract's 4.8:1 worst case.

---

# Variation 2: Instrument

**Design thesis.** The app is a measurement device operated by professionals, and its interface should behave like flight instrumentation: compact, tonal, monospace where precision matters, color spent only on signal. Surfaces separate by luminance steps rather than borders or shadows; the type scale drops to a 14px base; IDs, scores, and technique codes set in mono. It flatters the consultant who lives in the ATT&CK matrix eight hours a day and reads density as respect. Dark is the primary mode and was designed first; light is the derived daytime variant. Clients see a calm, quiet version of the same instrument, not a different product.

## Tokens: light

```css
:root {
  /* ----- Surface (tonal steps do the separating) ----- */
  --surface-canvas: #e9edf2;
  --surface-card: #f7f9fb;
  --surface-raised: #ffffff;
  --surface-sunken: #dce2ea;
  --surface-overlay: rgba(9, 13, 20, 0.6);

  /* ----- Ink ----- */
  --ink-primary: #10161f;
  --ink-secondary: #3b4557;
  --ink-tertiary: #525d74; /* 5.07:1 on sunken, 6.26:1 on card */
  --ink-on-accent: #ffffff;
  --ink-disabled: #9aa4b5;

  /* ----- Border (sparse; inputs and focus only) ----- */
  --border-subtle: #d4dae4;
  --border-default: #c2cad7;
  --border-strong: #67748b; /* 4.47:1 on card */
  --border-focus: #1256c4;

  /* ----- Brand (instrument blue) ----- */
  --brand-50: #e4edfb;
  --brand-100: #c8dcf8;
  --brand-300: #6d9de8;
  --brand-500: #1256c4; /* 6.31:1 as text on card; white on it 6.66:1 */
  --brand-600: #0e46a0;
  --brand-700: #0b3880;

  /* ----- Status ----- */
  --status-success-bg: #d7f0e0;
  --status-success-fg: #176440; /* 5.94:1 */
  --status-success-border: #7cc79c;
  --status-warning-bg: #fceec6;
  --status-warning-fg: #7c5a02; /* 5.48:1 */
  --status-warning-border: #e2bd54;
  --status-danger-bg: #fbdfdd;
  --status-danger-fg: #ab2028; /* 5.63:1 */
  --status-danger-border: #ef968f;
  --status-info-bg: #dae9fc;
  --status-info-fg: #1257a2; /* 5.86:1 */
  --status-info-border: #88b6ea;
  --status-neutral-bg: #e4e8ee;
  --status-neutral-fg: #49546c; /* 6.17:1 */
  --status-neutral-border: #b6c0cf;

  /* ----- Heat (sequential blue) ----- */
  --heat-1: #e4edfb;
  --heat-ink-1: #10161f; /* 15.39:1 */
  --heat-2: #b9d2f4;
  --heat-ink-2: #10161f; /* 11.75:1 */
  --heat-3: #82abe8;
  --heat-ink-3: #10161f; /*  7.73:1 */
  --heat-4: #2f63be;
  --heat-ink-4: #ffffff; /*  5.75:1 */
  --heat-5: #123f85;
  --heat-ink-5: #ffffff; /* 10.12:1 */

  /* ----- Risk tiers (highest chroma of the three systems) ----- */
  --tier-negligible-bg: #e4e8ee;
  --tier-negligible-fg: #49546c; /* 6.17:1 */
  --tier-low-bg: #a9dfbc;
  --tier-low-fg: #114d2b; /* 6.59:1 */
  --tier-medium-bg: #f4d44f;
  --tier-medium-fg: #574400; /* 6.44:1 */
  --tier-high-bg: #f2a55b;
  --tier-high-fg: #6b3305; /* 4.91:1 */
  --tier-critical-bg: #d92d3a;
  --tier-critical-fg: #ffffff; /* 4.79:1 */

  /* ----- Type (compressed scale, 14px base) ----- */
  --font-sans:
    "IBM Plex Sans", "Segoe UI", ui-sans-serif, system-ui, Arial, sans-serif;
  --font-mono:
    "IBM Plex Mono", ui-monospace, "Cascadia Mono", Menlo, Consolas, monospace;

  --text-xs: 0.6875rem; /* 11px */
  --text-sm: 0.8125rem; /* 13px */
  --text-base: 0.875rem; /* 14px */
  --text-lg: 1rem;
  --text-xl: 1.125rem;
  --text-2xl: 1.375rem;
  --text-3xl: 1.625rem;
  --text-4xl: 2rem;
  --text-display: 2.5rem;

  --leading-tight: 1.15;
  --leading-snug: 1.3;
  --leading-normal: 1.45;
  --leading-relaxed: 1.55;

  /* ----- Spacing (grid unchanged; components use smaller steps) ----- */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* ----- Radii (tight machining) ----- */
  --radius-xs: 1px;
  --radius-sm: 2px;
  --radius-md: 3px;
  --radius-lg: 4px;
  --radius-xl: 6px;
  --radius-pill: 9999px;

  /* ----- Shadows (tonal model: overlays only) ----- */
  --shadow-sm: none;
  --shadow-md: 0 2px 6px rgba(13, 19, 32, 0.1);
  --shadow-lg: 0 8px 24px rgba(13, 19, 32, 0.18);

  /* ----- Motion (instrument-quick) ----- */
  --motion-duration-fast: 90ms;
  --motion-duration: 140ms;
  --motion-ease: cubic-bezier(0.2, 0.7, 0.2, 1);

  --z-base: 0;
  --z-overlay: 50;
  --z-toast: 80;
  --z-modal: 100;
}
```

## Tokens: dark (the primary mode)

```css
:root[data-theme="dark"] {
  --surface-canvas: #0d1219;
  --surface-card: #151c26;
  --surface-raised: #1c2634;
  --surface-sunken: #080c12;
  --surface-overlay: rgba(0, 0, 0, 0.65);

  --ink-primary: #e8edf4;
  --ink-secondary: #b0bbcb;
  --ink-tertiary: #8794a8; /* 5.57:1 on card, 4.96:1 on raised */
  --ink-on-accent: #0a0f16; /* brand fills are light in dark mode */
  --ink-disabled: #4f5b6e;

  --border-subtle: #202939;
  --border-default: #2a3547;
  --border-strong: #5e6d85; /* 3.26:1 on card */
  --border-focus: #7aaaf3;

  --brand-50: #14253e;
  --brand-100: #1a3154;
  --brand-300: #3a71c9;
  --brand-500: #7aaaf3; /* 7.24:1 as text on card; on-accent on it 8.12:1 */
  --brand-600: #9dc0f7; /* 8.30:1 on brand-50 */
  --brand-700: #c1d7fb;

  --status-success-bg: #10301f;
  --status-success-fg: #57cf92; /* 7.34:1 */
  --status-success-border: #1f5c3b;
  --status-warning-bg: #302708;
  --status-warning-fg: #dcb141; /* 7.33:1 */
  --status-warning-border: #665012;
  --status-danger-bg: #3a151a;
  --status-danger-fg: #f28b85; /* 6.76:1 */
  --status-danger-border: #77262c;
  --status-info-bg: #10263e;
  --status-info-fg: #77aef2; /* 6.66:1 */
  --status-info-border: #2a5793;
  --status-neutral-bg: #1c2431;
  --status-neutral-fg: #a3b0c4; /* 7.11:1 */
  --status-neutral-border: #3c4759;

  --heat-1: #131c2b;
  --heat-ink-1: #e8edf4; /* 14.53:1 */
  --heat-2: #1a2c4a;
  --heat-ink-2: #e8edf4; /* 11.88:1 */
  --heat-3: #1f4066;
  --heat-ink-3: #e8edf4; /*  9.00:1 */
  --heat-4: #2f62a6;
  --heat-ink-4: #e8edf4; /*  5.22:1 */
  --heat-5: #4e8ede;
  --heat-ink-5: #0a0f16; /*  5.72:1 */

  --tier-negligible-bg: #1c2431;
  --tier-negligible-fg: #a3b0c4; /* 7.11:1 */
  --tier-low-bg: #1a4a2f;
  --tier-low-fg: #8fe0b0; /* 6.52:1 */
  --tier-medium-bg: #4a3d05;
  --tier-medium-fg: #ecd056; /* 7.00:1 */
  --tier-high-bg: #572a08;
  --tier-high-fg: #f5aa6d; /* 6.24:1 */
  --tier-critical-bg: #5c1216;
  --tier-critical-fg: #ff9c96; /* 6.73:1 */

  --shadow-sm: none;
  --shadow-md: 0 0 0 1px #2a3547;
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px #2a3547;
}
```

What changes conceptually in dark: this is the native mode, so the tonal ladder is the design rather than a translation. Elevation is literal luminance (sunken #080c12 → canvas #0d1219 → card #151c26 → raised #1c2634); shadows disappear and 1px rims on overlays replace them, because a shadow on near-black is invisible. Saturated status fills invert their construction: light mode is "dark saturated text on pale tint", dark mode is "bright saturated text on deep tint", never a solid saturated slab, which would bloom on dark surfaces. The heat ramp re-tunes rather than flips: mid-steps drop chroma and darken so the light `--ink-primary` stays AA through step 4, with the ink switch happening one step later than in light mode (after step 4, not step 3).

## Type system

- **One family**: IBM Plex Sans (self-hosted 400/500/600), fallback Segoe UI, Arial. Plex was drawn for terminals and screens and pairs natively with Plex Mono.
- **Mono is a first-class citizen**: IBM Plex Mono (self-hosted 400/500) for technique codes, scores, timestamps, and audit hashes. The `AttackMatrix` already sets codes in `font-mono`; this variation extends that to every numeric table column.
- **Scale**: compressed as tokenized above; 14px body, 13px in tables, 11px microtext. Headings gain little size but use weight (600) and letterspacing (0.02em on uppercase panel labels) to mark rank. Pairing rationale: sans for reading, mono for evidence; the mono column is the signature of the system.

## Component treatment

- **Data tables**: 32px rows (`py-1.5`), 13px body, mono right-aligned numerics. Vertical 1px `--border-subtle` column rules ON (the one variation that wants them, for cross-row scanning). Header keeps the sunken fill, 11px uppercase. Sticky header stays; the ATT&CK matrix additionally gets a sticky first column. Row hover `--surface-sunken`; selected row `--brand-50`.
- **Questionnaire question card**: compact block on card surface, prompt 14px/600. The score_0_2, yes_no, and tristate options become a joined segmented control, 32px tall, 1px shared borders, selected segment `--brand-50` fill with a 2px `--brand-500` bottom edge. Autosave status renders in 11px mono ("saved 12:04:31").
- **Status pills**: square chips. `StatusPill` swaps `rounded-pill` for `rounded-sm` and the label goes 11px mono uppercase; dot always on. In dense tables the chip collapses to dot plus code (`COV`, `GAP`) with the full label in `title`.
- **Heatmap cells**: flat fills, 2px canvas gaps, no radius, value in 11px mono in every occupied cell. Unscored cells get a 45-degree hatch texture instead of gray fill so "no data" never reads as "low".
- **Workspace stepper**: a horizontal rail of 2px underline segments; current segment `--brand-500`, completed `--status-success-fg`, upcoming `--border-default`. Labels 12px. No circles, no chips; the rail takes 24px of vertical space instead of today's 40+.
- **Cards/panels**: tonal. Card fill on canvas with no border and no shadow; `Card.tsx` drops the `border-border-subtle` class when this theme ships. Panel headers keep a single 1px `--border-subtle` bottom rule. `CardBody` padding drops to `px-4 py-3`.
- **Buttons**: 28px height, 3px radius, 13px label. Primary `--brand-500` fill; secondary tonal `--surface-sunken` fill with `--ink-primary` text; destructive is a `--status-danger-fg` outline, filling only on hover.
- **Form inputs**: `--surface-raised` field (white in light, #1c2634 in dark) with 1px `--border-default`, 32px height, 3px radius. Numeric inputs set in mono.

## Heatmap ramp (summary table)

| Step        | Light fill | Light ink | Ratio | Dark fill | Dark ink | Ratio |
| ----------- | ---------- | --------- | ----- | --------- | -------- | ----- |
| 1 (0-20%)   | #e4edfb    | #10161f   | 15.39 | #131c2b   | #e8edf4  | 14.53 |
| 2           | #b9d2f4    | #10161f   | 11.75 | #1a2c4a   | #e8edf4  | 11.88 |
| 3           | #82abe8    | #10161f   | 7.73  | #1f4066   | #e8edf4  | 9.00  |
| 4           | #2f63be    | #ffffff   | 5.75  | #2f62a6   | #e8edf4  | 5.22  |
| 5 (80-100%) | #123f85    | #ffffff   | 10.12 | #4e8ede   | #0a0f16  | 5.72  |

Risk tiers are the boldest of the three systems: critical is a true red slab (#d92d3a with white text, 4.79:1 in light; #ff9c96 on #5c1216, 6.73:1 in dark). High and medium keep dark text on saturated fills (4.91:1 and 6.44:1). Every tier still prints its count, so the encoding never rests on hue alone.

## What it costs

- **The global scale change is the big one.** Dropping `--text-base` to 14px reflows every screen. Nothing in the e2e suite asserts pixel layout, but all six admin workspaces need an eyeball pass for truncation, and the marketing/auth pages will want per-page size bumps (they inherit the compressed scale otherwise).
- The segmented control for `QuestionField` is genuine component work, the largest single item (three input types across admin and self-assessment questionnaires).
- `Card.tsx` and `DataTable.tsx` change surface strategy (border removal, column rules, sticky first column). `StatusPill.tsx` changes shape and label casing.
- Dark-first means the axe sweep must add the dark pass before this variation is credible at all; both palettes above are fully verified, so the risk is regressions in components with hard-coded colors, not the tokens.
- Exporters: the saturated tier fills must be mirrored, and the DOCX/PDF templates should keep the light-mode values (documents are read on paper; the dark ramp is screen-only).
- Axe risk: moderate, from density rather than color. 11px microtext is above the AA contrast bar (contrast is size-independent once past 4.5:1) but small type invites cramped hit targets; interactive chips must keep 24px minimum target height even when visually 20px.

---

# Variation 3: Counsel

**Design thesis.** The app is the client-facing face of a premium advisory practice, and it should carry the composure of a well-run engagement: soft elevation, generous whitespace, a confident geometric sans, one deep petrol accent, status told in calm tinted pills. Surfaces float on a cool-tinted canvas with layered shadows instead of rules. It flatters the client executive who equates polish with competence, and the partner presenting the dashboard on a projector. Dark mode is the boardroom at dusk: the same soft hierarchy expressed through lighter raised surfaces and rim light, tuned for presentations rather than late-night data entry.

## Tokens: light

```css
:root {
  /* ----- Surface ----- */
  --surface-canvas: #f2f5f5;
  --surface-card: #ffffff;
  --surface-raised: #ffffff;
  --surface-sunken: #e7edee;
  --surface-overlay: rgba(10, 25, 24, 0.5);

  /* ----- Ink ----- */
  --ink-primary: #122023;
  --ink-secondary: #3f5257;
  --ink-tertiary: #566569; /* 5.13:1 on sunken, 6.07:1 on card */
  --ink-on-accent: #ffffff;
  --ink-disabled: #a7b4b6;

  /* ----- Border (mostly retired; shadows carry surfaces) ----- */
  --border-subtle: #e3eaea;
  --border-default: #d2dcdc;
  --border-strong: #7f9195; /* 3.29:1 on white; used for input boundaries */
  --border-focus: #0c6058;

  /* ----- Brand (petrol) ----- */
  --brand-50: #e3f1ef;
  --brand-100: #c2e3df;
  --brand-300: #43998f;
  --brand-500: #0c6058; /* 7.42:1 as text on card; white on it 7.42:1 */
  --brand-600: #094b45;
  --brand-700: #073a35;

  /* ----- Status (info moves to indigo so it never collides with brand) ----- */
  --status-success-bg: #dcf2e3;
  --status-success-fg: #196b40; /* 5.55:1 */
  --status-success-border: #a0d8b4;
  --status-warning-bg: #fcefcb;
  --status-warning-fg: #825a06; /* 5.37:1 */
  --status-warning-border: #eac86d;
  --status-danger-bg: #fbe2e1;
  --status-danger-fg: #ad2331; /* 5.57:1 */
  --status-danger-border: #f2acb0;
  --status-info-bg: #e5e9fc;
  --status-info-fg: #3a49ae; /* 6.34:1 */
  --status-info-border: #b7c0f2;
  --status-neutral-bg: #e9eef0;
  --status-neutral-fg: #4c5e63; /* 5.81:1 */
  --status-neutral-border: #ccd8db;

  /* ----- Heat (sequential petrol) ----- */
  --heat-1: #e3f1ef;
  --heat-ink-1: #122023; /* 14.40:1 */
  --heat-2: #bcdfda;
  --heat-ink-2: #122023; /* 11.70:1 */
  --heat-3: #8ac4bd;
  --heat-ink-3: #122023; /*  8.52:1 */
  --heat-4: #4c9c93;
  --heat-ink-4: #122023; /*  5.16:1 */
  --heat-5: #12645c;
  --heat-ink-5: #ffffff; /*  6.99:1 */

  /* ----- Risk tiers ----- */
  --tier-negligible-bg: #eaf0f1;
  --tier-negligible-fg: #4c5c60; /* 6.06:1 */
  --tier-low-bg: #d3ecd9;
  --tier-low-fg: #17603b; /* 6.05:1 */
  --tier-medium-bg: #fbe8a9;
  --tier-medium-fg: #6d5405; /* 5.90:1 */
  --tier-high-bg: #f9d2a6;
  --tier-high-fg: #82400c; /* 5.51:1 */
  --tier-critical-bg: #f5b7b2;
  --tier-critical-fg: #92211f; /* 5.00:1 */

  /* ----- Type ----- */
  --font-sans:
    "Manrope", "Segoe UI", ui-sans-serif, system-ui, "Helvetica Neue", Arial,
    sans-serif;
  --font-mono:
    ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", Menlo, Consolas,
    monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;
  --text-4xl: 2.5rem;
  --text-display: 3.25rem;

  --leading-tight: 1.15;
  --leading-snug: 1.35;
  --leading-normal: 1.5;
  --leading-relaxed: 1.7;

  /* ----- Spacing (unchanged) ----- */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  /* ----- Radii (soft geometry) ----- */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;
  --radius-pill: 9999px;

  /* ----- Shadows (layered lift replaces borders) ----- */
  --shadow-sm:
    0 1px 2px rgba(13, 32, 35, 0.06), 0 2px 8px rgba(13, 32, 35, 0.05);
  --shadow-md:
    0 2px 4px rgba(13, 32, 35, 0.05), 0 10px 24px -6px rgba(13, 32, 35, 0.1);
  --shadow-lg:
    0 6px 12px rgba(13, 32, 35, 0.06), 0 24px 48px -12px rgba(13, 32, 35, 0.16);

  /* ----- Motion (composed, slightly slower) ----- */
  --motion-duration-fast: 160ms;
  --motion-duration: 220ms;
  --motion-ease: cubic-bezier(0.2, 0.7, 0.2, 1);

  --z-base: 0;
  --z-overlay: 50;
  --z-toast: 80;
  --z-modal: 100;
}
```

## Tokens: dark

```css
:root[data-theme="dark"] {
  --surface-canvas: #0e1516;
  --surface-card: #172223;
  --surface-raised: #1d2b2c;
  --surface-sunken: #0a1011;
  --surface-overlay: rgba(0, 0, 0, 0.55);

  --ink-primary: #e6eeee;
  --ink-secondary: #b2c2c3;
  --ink-tertiary: #8ba0a2; /* 5.93:1 on card, 5.33:1 on raised */
  --ink-on-accent: #071716;
  --ink-disabled: #536568;

  --border-subtle: #233637;
  --border-default: #2c4344;
  --border-strong: #5f797c; /* 3.50:1 on card */
  --border-focus: #4bb3a8;

  --brand-50: #12312e;
  --brand-100: #173f3b;
  --brand-300: #2c7f77;
  --brand-500: #4bb3a8; /* 6.45:1 as text on card; on-accent on it 7.27:1 */
  --brand-600: #74c8bf; /* 7.15:1 on brand-50 */
  --brand-700: #9cdad3;

  --status-success-bg: #123023;
  --status-success-fg: #6fcf9f; /* 7.54:1 */
  --status-success-border: #245c41;
  --status-warning-bg: #332a0c;
  --status-warning-fg: #dcb959; /* 7.53:1 */
  --status-warning-border: #665318;
  --status-danger-bg: #3b181d;
  --status-danger-fg: #f2938f; /* 7.00:1 */
  --status-danger-border: #782a31;
  --status-info-bg: #191f3d;
  --status-info-fg: #9daef5; /* 7.52:1 */
  --status-info-border: #38428c;
  --status-neutral-bg: #1b2527;
  --status-neutral-fg: #9fb1b3; /* 7.02:1 */
  --status-neutral-border: #3a4a4c;

  --heat-1: #12201f;
  --heat-ink-1: #e6eeee; /* 14.24:1 */
  --heat-2: #163632;
  --heat-ink-2: #e6eeee; /* 11.09:1 */
  --heat-3: #1d504a;
  --heat-ink-3: #e6eeee; /*  7.76:1 */
  --heat-4: #297067;
  --heat-ink-4: #e6eeee; /*  4.94:1 */
  --heat-5: #45a89d;
  --heat-ink-5: #071716; /*  6.42:1 */

  --tier-negligible-bg: #1b2527;
  --tier-negligible-fg: #9fb1b3; /* 7.02:1 */
  --tier-low-bg: #14402b;
  --tier-low-fg: #90dbb0; /* 7.20:1 */
  --tier-medium-bg: #43370a;
  --tier-medium-fg: #e6c65b; /* 7.04:1 */
  --tier-high-bg: #4d2a0e;
  --tier-high-fg: #f3ac71; /* 6.62:1 */
  --tier-critical-bg: #521a1c;
  --tier-critical-fg: #fb9d97; /* 6.81:1 */

  /* Shadows do nothing on near-black; rim light replaces lift */
  --shadow-sm: 0 0 0 1px #233637;
  --shadow-md: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 0 1px #233637;
  --shadow-lg: 0 24px 48px rgba(0, 0, 0, 0.55), 0 0 0 1px #2c4344;
}
```

What changes conceptually in dark: the elevation story flips medium. Light mode says "closer objects cast shadows"; dark mode says "closer objects catch light", so `--surface-raised` is the lightest surface and every shadow token gains a 1px rim, because a drop shadow on #0e1516 is invisible. Status pills keep their soft-tint construction but the tints go deep and the text goes bright, and the pill ring border does more of the work since shadows no longer separate the pill from a card. The heat ramp keeps hue and reverses value direction, with step 4 darkened until light primary ink holds 4.94:1.

## Type system

- **One family**: Manrope, self-hosted (400, 500, 700, 800), fallback Segoe UI. A geometric sans with open apertures that stays legible at 13px in tables and turns confident at display sizes.
- **Headings**: 700 to 800 weight with -0.02em tracking at `--text-2xl` and above, -0.01em below. The bumped 3xl (2rem) and 4xl (2.5rem) give the client dashboard and report heroes real presence.
- **Body**: 400 at 16px, `--leading-normal` 1.5; long-form guidance uses `--leading-relaxed` 1.7.
- Pairing rationale: a single family with a wide weight axis keeps the surface calm; rank is expressed by weight and space, never by switching voices. Mono stays reserved for identifiers.

## Component treatment

- **Data tables**: the container becomes a floating panel (radius `--radius-lg`, `--shadow-sm`, no outer border). Header row sits on white with 12px/600 labels, 0.04em tracking, and a 2px `--brand-100` bottom rule instead of a fill. 48px rows, first column at weight 600, hover tint `--brand-50`. Zebra stays off.
- **Questionnaire question card**: each question gets its own soft card (radius `--radius-lg`, `--shadow-sm`, `--space-6` padding), prompt 16px/700. Options are pill chips; selected chip fills `--brand-50` with a 1.5px `--brand-500` ring and a check glyph. Section completion shows as "7 of 12" text next to the section tab, no ring gauges.
- **Status pills**: fully round, tinted, `withDot` default on. The ring border stays but the border tokens above sit close to the tint, so the pill reads as one soft object. 12px/600 labels, sentence case.
- **Heatmap cells**: rounded `--radius-xs` (4px) cells with 4px canvas gaps, values at weight 600, a legend row of labeled chips under every matrix. The gap-and-radius treatment is the signature difference from Ledger's ruled grid and Instrument's flat mosaic.
- **Workspace stepper**: pill chips joined by a 2px connector line; completed chips tint success, current chip fills `--brand-500` with white text, upcoming chips are white with `--border-default`. Numerals stay in circles (this variation keeps them).
- **Cards/panels**: `--shadow-sm` and no border; `Card.tsx` drops `border-border-subtle` for this theme. `CardHeader` loses its bottom hairline; whitespace separates header from body. Radius `--radius-lg`.
- **Buttons**: 40px height. Primary is a `--brand-500` fill, pill-shaped on client surfaces, `--radius-md` in admin workspaces. Secondary is `--brand-50` fill with `--brand-600` text (8.60:1). Tertiary is plain `--brand-500` text.
- **Form inputs**: `--surface-sunken` fill, 1px `--border-strong` boundary (3.29:1 on white, clearing the 3:1 non-text minimum), radius `--radius-md`, 40px height; on focus the field goes white with a 2px `--border-focus` ring.

## Heatmap ramp (summary table)

| Step        | Light fill | Light ink | Ratio | Dark fill | Dark ink | Ratio |
| ----------- | ---------- | --------- | ----- | --------- | -------- | ----- |
| 1 (0-20%)   | #e3f1ef    | #122023   | 14.40 | #12201f   | #e6eeee  | 14.24 |
| 2           | #bcdfda    | #122023   | 11.70 | #163632   | #e6eeee  | 11.09 |
| 3           | #8ac4bd    | #122023   | 8.52  | #1d504a   | #e6eeee  | 7.76  |
| 4           | #4c9c93    | #122023   | 5.16  | #297067   | #e6eeee  | 4.94  |
| 5 (80-100%) | #12645c    | #ffffff   | 6.99  | #45a89d   | #071716  | 6.42  |

Risk tiers keep soft mid-strength tints with dark saturated text; the tightest pairing is critical in light mode at 5.00:1. Because the fills are gentler than Instrument's, the printed count and the legend do more of the severity work, which is why both are mandatory in this variation's component rules.

## What it costs

- The radius jump ripples everywhere `rounded-md`/`rounded-lg` utilities appear: 10px corners on the ATT&CK matrix's tiny technique buttons look swollen, so dense admin widgets (AttackMatrix cells, ZtStagePicker, TierPicker chips) need spot overrides down to `--radius-xs`. Budget a pass over the six workspaces.
- Border removal is real work in the design system package: `Card.tsx`, `DataTable.tsx`, `Modal.tsx`, `SlideOver.tsx` all currently pair border plus shadow. Light mode must be checked for panels that lose their edge on the tinted canvas (shadow at 5 to 6% alpha is subtle on #f2f5f5); where a panel sits on sunken surface, keep a `--border-subtle` rim.
- Manrope self-hosting (four weights) plus a base-layer heading rule remapping 600 to 700/800.
- Info status moving to indigo needs a copy check anywhere "info" tone was leaning on brand-blue association; no e2e spec asserts color, so this is visual QA only.
- Exporters: soft tints print lighter than the current Tailwind-derived tiers; the DOCX/PDF templates must adopt the tier hexes above or the app will look calmer than the report it produces.
- Axe risk: low to moderate. All pairings verified; the watch item is non-text contrast (WCAG 1.4.11) once borders retire, which is why inputs get `--border-strong` explicitly and dark-mode shadows carry 1px rims.

---

# Comparison and recommendation

| Axis                    | Ledger                                                       | Instrument                                             | Counsel                                                 |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------- |
| Argument                | Instrument of record; the app looks like its own deliverable | Measurement console for daily operators                | Premium advisory engagement surface                     |
| Flatters                | The skeptical client reviewer                                | The consultant power user                              | The buying executive, the projector demo                |
| Type                    | Source Serif 4 headings over Inter body, tabular numerals    | IBM Plex Sans + Plex Mono, 14px base, compressed scale | Manrope alone, wide weight axis, larger display sizes   |
| Surface strategy        | Flat; hairline rules, zero lift                              | Tonal luminance steps, near-zero borders               | Layered soft shadows, borders retired                   |
| Corners                 | 0 to 4px, pills become tags                                  | 1 to 6px, machine-tight                                | 4 to 20px, soft                                         |
| Density                 | Editorial; roomier leading, 44px rows                        | Highest; 32px rows, 13px tables                        | Comfortable; 48px rows, generous padding                |
| Status color            | Printed tags, darker rings                                   | Square mono chips, dots, hatch for no-data             | Soft round pills, dot default                           |
| Heatmap reads as        | Ruled survey table                                           | Flat saturated mosaic                                  | Rounded soft matrix with legend                         |
| Tier "critical" (light) | #85271a on #e9b0a5, 4.87:1                                   | white on #d92d3a, 4.79:1                               | #92211f on #f5b7b2, 5.00:1                              |
| Dark concept            | Reading room; warm charcoal, rules lighten                   | Native mode; luminance ladder is the design            | Boardroom; raised surfaces catch rim light              |
| Chrome carried          | Least                                                        | Low, but instrument-labeled                            | Most (shadows, tints, connectors)                       |
| Biggest adoption cost   | Pill-to-tag reshape + serif hosting                          | Global 14px reflow + segmented controls                | Radius ripple + border retirement across the DS package |
| Axe-sweep risk          | Low                                                          | Moderate (density, hit targets)                        | Low-moderate (1.4.11 after border removal)              |
| Export fidelity         | Highest; screen already looks like the PDF                   | Good on data, but screen is denser than any report     | Good, but polish gap if templates lag                   |

**Recommendation: Ledger.**

The stated goal is credibility with skeptical clients who will challenge the numbers, and the deliverable they challenge is a PDF, a DOCX, or a printed XLSX. Ledger is the only system where the screen, the exported report, and the projected walkthrough share one typographic voice, so the client never experiences a gap between "the tool" and "the document we are being asked to trust". Its restraint is itself the argument: ruled tables, tabular numerals, muted tier fills that survive a grayscale photocopier, status as printed tags rather than colored candy. Serif headings signal a written record, and written records are what assessment clients pay for.

Instrument is the best system for the consultants and the worst for the audience that matters here; a client shown a dense mono console concludes they are looking at the vendor's internal tooling. Counsel is the most conventionally attractive and the easiest to sell in a screenshot, but polish is exactly the axis a skeptical reviewer discounts; rounded pills and floating cards read as marketing, and its soft tier fills lean hardest on legends to stay defensible. Ledger's costs are real (the pill reshape, serif hosting, warm-palette audit) but they are one-time visual QA, not structural rework, and its measured worst-case ratios (4.87:1 tightest, most pairings above 6:1) leave more accessibility headroom than the current system's 4.8:1 floor.

If consultant fatigue with Ledger's editorial density becomes a complaint, the correct move is Ledger's tokens with Instrument's table row height in admin workspaces, which the shared token contract makes a two-line component change, not a fourth theme.
