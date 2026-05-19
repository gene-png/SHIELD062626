import type { Config } from "tailwindcss";

// Stage-5 baseline. Round 6 Design Contract tokens (palette, typography,
// spacing scale) land in stage 6 (packages/design-system) and replace
// these defaults wholesale.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Inter", "sans-serif"],
      },
      colors: {
        // Provisional neutral palette - replaced by Round 6 tokens in stage 6.
        ink: {
          50: "#f7f8fa",
          100: "#eceef2",
          200: "#d6dae3",
          400: "#8b94a6",
          600: "#475063",
          800: "#1f2533",
          900: "#0e1220",
        },
        navy: {
          500: "#1b3a7a",
          600: "#142d62",
          700: "#0e224b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
