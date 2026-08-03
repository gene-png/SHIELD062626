// WCAG 2.1 contrast checker for the three SHIELD design variations.
// Every pairing claimed in design-variations.md must appear here and pass.

function lum(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  const f = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function ratio(a, b) {
  const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

// pairs: [label, fg, bg, min]
const suites = {
  // ---------------- V1 LEDGER light ----------------
  "LEDGER light": (() => {
    const canvas = "#f7f5f0", card = "#fffdf8", sunken = "#efece3";
    const ip = "#211d14", is = "#4c473b", it = "#6b6557", onAcc = "#fffdf8";
    const b50 = "#edf1ea", b500 = "#2b5c44", b600 = "#204832", b700 = "#173425";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/sunken", ip, sunken, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/sunken", it, sunken, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#2c633f", "#e9f1e7", 4.5],
      ["succ fg/card", "#2c633f", card, 4.5],
      ["warn fg/bg", "#7d5a0e", "#f7edd2", 4.5],
      ["warn fg/card", "#7d5a0e", card, 4.5],
      ["dang fg/bg", "#99311f", "#f6e3dd", 4.5],
      ["dang fg/card", "#99311f", card, 4.5],
      ["info fg/bg", "#31567a", "#e6ecf3", 4.5],
      ["info fg/card", "#31567a", card, 4.5],
      ["neut fg/bg", "#5a5545", "#edeade", 4.5],
      ["neut fg/card", "#5a5545", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#2c633f", 4.5],
      ["tier neg", "#5a5545", "#eeebe0", 4.5],
      ["tier low", "#3e5c2a", "#dfe9d5", 4.5],
      ["tier med", "#6c5410", "#f1e3b3", 4.5],
      ["tier high", "#7d3f10", "#f0cba2", 4.5],
      ["tier crit", "#85271a", "#e9b0a5", 4.5],
      ["heat1 ink", ip, "#eaf0e6", 4.5],
      ["heat2 ink", ip, "#c9dac2", 4.5],
      ["heat3 ink", ip, "#a3c19d", 4.5],
      ["heat4 ink", ip, "#6f9d74", 4.5],
      ["heat5 ink", onAcc, "#35664b", 4.5],
    ];
  })(),
  // ---------------- V1 LEDGER dark ----------------
  "LEDGER dark": (() => {
    const canvas = "#17140e", card = "#201c14", raised = "#272218", sunken = "#100d09";
    const ip = "#ece5d4", is = "#c3bba6", it = "#a09781", onAcc = "#171310";
    const b50 = "#232e24", b500 = "#7fb08d", b600 = "#9cc4a6", b700 = "#bcd8c2";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/raised", ip, raised, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/raised", it, raised, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#9ac79c", "#1d2b1e", 4.5],
      ["succ fg/card", "#9ac79c", card, 4.5],
      ["warn fg/bg", "#d5b264", "#2e2611", 4.5],
      ["warn fg/card", "#d5b264", card, 4.5],
      ["dang fg/bg", "#e39a83", "#331b14", 4.5],
      ["dang fg/card", "#e39a83", card, 4.5],
      ["info fg/bg", "#9db9d6", "#1b2530", 4.5],
      ["info fg/card", "#9db9d6", card, 4.5],
      ["neut fg/bg", "#b5ac93", "#262215", 4.5],
      ["neut fg/card", "#b5ac93", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#9ac79c", 4.5],
      ["tier neg", "#b5ac93", "#262215", 4.5],
      ["tier low", "#a9d09e", "#223320", 4.5],
      ["tier med", "#d9bd57", "#393112", 4.5],
      ["tier high", "#e2a263", "#402813", 4.5],
      ["tier crit", "#ee9f86", "#44201a", 4.5],
      ["heat1 ink", ip, "#20281f", 4.5],
      ["heat2 ink", ip, "#2b3d2c", 4.5],
      ["heat3 ink", ip, "#33503a", 4.5],
      ["heat4 ink", ip, "#47694c", 4.5],
      ["heat5 ink", onAcc, "#74ab7e", 4.5],
    ];
  })(),
  // ---------------- V2 INSTRUMENT light ----------------
  "INSTRUMENT light": (() => {
    const canvas = "#e9edf2", card = "#f7f9fb", raised = "#ffffff", sunken = "#dce2ea";
    const ip = "#10161f", is = "#3b4557", it = "#525d74", onAcc = "#ffffff";
    const b50 = "#e4edfb", b500 = "#1256c4", b600 = "#0e46a0", b700 = "#0b3880";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/sunken", ip, sunken, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/sunken", it, sunken, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["ink-tertiary/raised", it, raised, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#176440", "#d7f0e0", 4.5],
      ["succ fg/card", "#176440", card, 4.5],
      ["warn fg/bg", "#7c5a02", "#fceec6", 4.5],
      ["warn fg/card", "#7c5a02", card, 4.5],
      ["dang fg/bg", "#ab2028", "#fbdfdd", 4.5],
      ["dang fg/card", "#ab2028", card, 4.5],
      ["info fg/bg", "#1257a2", "#dae9fc", 4.5],
      ["info fg/card", "#1257a2", card, 4.5],
      ["neut fg/bg", "#49546c", "#e4e8ee", 4.5],
      ["neut fg/card", "#49546c", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#176440", 4.5],
      ["tier neg", "#49546c", "#e4e8ee", 4.5],
      ["tier low", "#114d2b", "#a9dfbc", 4.5],
      ["tier med", "#574400", "#f4d44f", 4.5],
      ["tier high", "#6b3305", "#f2a55b", 4.5],
      ["tier crit", "#ffffff", "#d92d3a", 4.5],
      ["heat1 ink", ip, "#e4edfb", 4.5],
      ["heat2 ink", ip, "#b9d2f4", 4.5],
      ["heat3 ink", ip, "#82abe8", 4.5],
      ["heat4 ink", onAcc, "#2f63be", 4.5],
      ["heat5 ink", onAcc, "#123f85", 4.5],
    ];
  })(),
  // ---------------- V2 INSTRUMENT dark ----------------
  "INSTRUMENT dark": (() => {
    const canvas = "#0d1219", card = "#151c26", raised = "#1c2634", sunken = "#080c12";
    const ip = "#e8edf4", is = "#b0bbcb", it = "#8794a8", onAcc = "#0a0f16";
    const b50 = "#14253e", b500 = "#7aaaf3", b600 = "#9dc0f7", b700 = "#c1d7fb";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/raised", ip, raised, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/raised", it, raised, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#57cf92", "#10301f", 4.5],
      ["succ fg/card", "#57cf92", card, 4.5],
      ["warn fg/bg", "#dcb141", "#302708", 4.5],
      ["warn fg/card", "#dcb141", card, 4.5],
      ["dang fg/bg", "#f28b85", "#3a151a", 4.5],
      ["dang fg/card", "#f28b85", card, 4.5],
      ["info fg/bg", "#77aef2", "#10263e", 4.5],
      ["info fg/card", "#77aef2", card, 4.5],
      ["neut fg/bg", "#a3b0c4", "#1c2431", 4.5],
      ["neut fg/card", "#a3b0c4", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#57cf92", 4.5],
      ["tier neg", "#a3b0c4", "#1c2431", 4.5],
      ["tier low", "#8fe0b0", "#1a4a2f", 4.5],
      ["tier med", "#ecd056", "#4a3d05", 4.5],
      ["tier high", "#f5aa6d", "#572a08", 4.5],
      ["tier crit", "#ff9c96", "#5c1216", 4.5],
      ["heat1 ink", ip, "#131c2b", 4.5],
      ["heat2 ink", ip, "#1a2c4a", 4.5],
      ["heat3 ink", ip, "#1f4066", 4.5],
      ["heat4 ink", ip, "#2f62a6", 4.5],
      ["heat5 ink", onAcc, "#4e8ede", 4.5],
    ];
  })(),
  // ---------------- V3 COUNSEL light ----------------
  "COUNSEL light": (() => {
    const canvas = "#f2f5f5", card = "#ffffff", sunken = "#e7edee";
    const ip = "#122023", is = "#3f5257", it = "#566569", onAcc = "#ffffff";
    const b50 = "#e3f1ef", b500 = "#0c6058", b600 = "#094b45", b700 = "#073a35";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/sunken", ip, sunken, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/sunken", it, sunken, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#196b40", "#dcf2e3", 4.5],
      ["succ fg/card", "#196b40", card, 4.5],
      ["warn fg/bg", "#825a06", "#fcefcb", 4.5],
      ["warn fg/card", "#825a06", card, 4.5],
      ["dang fg/bg", "#ad2331", "#fbe2e1", 4.5],
      ["dang fg/card", "#ad2331", card, 4.5],
      ["info fg/bg", "#3a49ae", "#e5e9fc", 4.5],
      ["info fg/card", "#3a49ae", card, 4.5],
      ["neut fg/bg", "#4c5e63", "#e9eef0", 4.5],
      ["neut fg/card", "#4c5e63", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#196b40", 4.5],
      ["tier neg", "#4c5c60", "#eaf0f1", 4.5],
      ["tier low", "#17603b", "#d3ecd9", 4.5],
      ["tier med", "#6d5405", "#fbe8a9", 4.5],
      ["tier high", "#82400c", "#f9d2a6", 4.5],
      ["tier crit", "#92211f", "#f5b7b2", 4.5],
      ["heat1 ink", ip, "#e3f1ef", 4.5],
      ["heat2 ink", ip, "#bcdfda", 4.5],
      ["heat3 ink", ip, "#8ac4bd", 4.5],
      ["heat4 ink", ip, "#4c9c93", 4.5],
      ["heat5 ink", onAcc, "#12645c", 4.5],
    ];
  })(),
  // ---------------- V3 COUNSEL dark ----------------
  "COUNSEL dark": (() => {
    const canvas = "#0e1516", card = "#172223", raised = "#1d2b2c", sunken = "#0a1011";
    const ip = "#e6eeee", is = "#b2c2c3", it = "#8ba0a2", onAcc = "#071716";
    const b50 = "#12312e", b500 = "#4bb3a8", b600 = "#74c8bf", b700 = "#9cdad3";
    return [
      ["ink-primary/canvas", ip, canvas, 4.5],
      ["ink-primary/card", ip, card, 4.5],
      ["ink-primary/raised", ip, raised, 4.5],
      ["ink-primary/brand-50", ip, b50, 4.5],
      ["ink-secondary/card", is, card, 4.5],
      ["ink-secondary/sunken", is, sunken, 4.5],
      ["ink-tertiary/card", it, card, 4.5],
      ["ink-tertiary/raised", it, raised, 4.5],
      ["ink-tertiary/canvas", it, canvas, 4.5],
      ["on-accent/brand-500", onAcc, b500, 4.5],
      ["on-accent/brand-600", onAcc, b600, 4.5],
      ["brand-500 text/card", b500, card, 4.5],
      ["brand-500 text/canvas", b500, canvas, 4.5],
      ["brand-600 text/card", b600, card, 4.5],
      ["brand-600/brand-50", b600, b50, 4.5],
      ["brand-700 text/card", b700, card, 4.5],
      ["focus/canvas (3:1)", b500, canvas, 3],
      ["succ fg/bg", "#6fcf9f", "#123023", 4.5],
      ["succ fg/card", "#6fcf9f", card, 4.5],
      ["warn fg/bg", "#dcb959", "#332a0c", 4.5],
      ["warn fg/card", "#dcb959", card, 4.5],
      ["dang fg/bg", "#f2938f", "#3b181d", 4.5],
      ["dang fg/card", "#f2938f", card, 4.5],
      ["info fg/bg", "#9daef5", "#191f3d", 4.5],
      ["info fg/card", "#9daef5", card, 4.5],
      ["neut fg/bg", "#9fb1b3", "#1b2527", 4.5],
      ["neut fg/card", "#9fb1b3", card, 4.5],
      ["on-accent/succ-fg (stepper)", onAcc, "#6fcf9f", 4.5],
      ["tier neg", "#9fb1b3", "#1b2527", 4.5],
      ["tier low", "#90dbb0", "#14402b", 4.5],
      ["tier med", "#e6c65b", "#43370a", 4.5],
      ["tier high", "#f3ac71", "#4d2a0e", 4.5],
      ["tier crit", "#fb9d97", "#521a1c", 4.5],
      ["heat1 ink", ip, "#12201f", 4.5],
      ["heat2 ink", ip, "#163632", 4.5],
      ["heat3 ink", ip, "#1d504a", 4.5],
      ["heat4 ink", ip, "#297067", 4.5],
      ["heat5 ink", onAcc, "#45a89d", 4.5],
    ];
  })(),
};

let fails = 0;
for (const [name, pairs] of Object.entries(suites)) {
  console.log(`\n=== ${name} ===`);
  for (const [label, fg, bg, min] of pairs) {
    const r = ratio(fg, bg);
    const ok = r >= min;
    if (!ok) fails++;
    console.log(
      `${ok ? "PASS" : "FAIL"}  ${r.toFixed(2).padStart(6)}  (min ${min})  ${label}  ${fg} on ${bg}`,
    );
  }
}
console.log(`\n${fails} failures`);
