// ESLint flat config (ESLint 9). Replaces the legacy .eslintrc.json.
// eslint-config-next 16 ships a native flat-config array at ./core-web-vitals
// that preserves the exact rule set the old `next/core-web-vitals` extends gave
// us (see the commit body for the print-config parity diff). ESLint 10 is
// deliberately deferred: no published Next lint stack runs on v10 yet
// (eslint-plugin-react 7.37.5 calls the removed context.getFilename(), and
// Next's parser trips eslint-scope's missing scopeManager.addGlobals).
const nextCoreWebVitals = require("eslint-config-next/core-web-vitals");

/** @type {import("eslint").Linter.Config[]} */
module.exports = [
  // Flat config has no built-in Next ignores; `next lint` used to add these.
  {
    ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"],
  },
  ...nextCoreWebVitals,
  // RULE PARITY: eslint-config-next 16 bundles eslint-plugin-react-hooks v6,
  // which enables 14 React-Compiler-era rules that the prior
  // `next/core-web-vitals` (react-hooks v4) did not. This migration is a
  // config-format change at rule parity, not a lint-policy expansion — the
  // new rules fire on existing effects/purity patterns and adopting them is a
  // source refactor out of scope here. Turn them off to hold the exact 47-rule
  // set from before; adopting the React Compiler rules is a future dedicated
  // task (see the T3 commit body for the print-config parity diff).
  {
    rules: {
      "react-hooks/config": "off",
      "react-hooks/error-boundaries": "off",
      "react-hooks/gating": "off",
      "react-hooks/globals": "off",
      "react-hooks/immutability": "off",
      "react-hooks/incompatible-library": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/purity": "off",
      "react-hooks/refs": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/set-state-in-render": "off",
      "react-hooks/static-components": "off",
      "react-hooks/unsupported-syntax": "off",
      "react-hooks/use-memo": "off",
    },
  },
];
