import "@testing-library/jest-dom/vitest";

import { readFileSync, readdirSync } from "node:fs";
// Node's own URL: the jsdom environment replaces the global one, and
// fileURLToPath rejects the object jsdom's URL returns.
import { fileURLToPath, URL as NodeUrl } from "node:url";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HowAiWorks, HOW_AI_WORKS_SERVICES } from "./HowAiWorks";

/**
 * S8 / D-037, both halves.
 *
 * The first describe covers the consultant-facing disclosure: it has to name
 * what AI drafts for the service it is mounted in, what code computes instead,
 * the redaction gate in front of every call, and the difference between fixture
 * and live mode. Copy that is only true in one mode would be the same defect
 * the fixture-mode banner had.
 *
 * The second describe is the client-silence guard. The acceptance criterion as
 * written ("the diff touches no client-surface file") is a property of a diff,
 * so no test run can fail it and doing nothing satisfies it. This reads the
 * client-surface sources instead and fails whenever AI vocabulary reaches any
 * of them, in this sprint or any later one.
 */

const SERVICES = HOW_AI_WORKS_SERVICES;

/** The disclosure wrapper, found by its accessible name. */
function disclosure(): HTMLElement {
  return screen.getByLabelText("How AI is used here");
}

describe("HowAiWorks disclosure", () => {
  it("covers drafts, computation, redaction, and fixture versus live", () => {
    render(<HowAiWorks service="attack" />);

    expect(disclosure()).toBeInTheDocument();

    expect(screen.getByText("What AI drafts here")).toBeInTheDocument();
    expect(screen.getByText("What code computes")).toBeInTheDocument();
    expect(screen.getByText("Before a prompt leaves")).toBeInTheDocument();
    expect(screen.getByText("Fixture mode and live mode")).toBeInTheDocument();

    // The redaction gate names the boundary, not a vague reassurance.
    expect(screen.getByText(/one redactor/i)).toBeInTheDocument();
    expect(screen.getByText(/placeholders/i)).toBeInTheDocument();

    // Both modes are described, so the copy is true whichever one is running.
    const modes = screen.getByText(/fixture mode, Run AI returns/i);
    expect(modes).toHaveTextContent(/no request leaves this deployment/i);
    expect(modes).toHaveTextContent(/live mode/i);

    // D-035 discipline: no acceptance state exists, so nothing may imply one.
    expect(screen.getByText(/carries no sign-off/i)).toBeInTheDocument();
    const body = disclosure().textContent ?? "";
    expect(body).not.toMatch(/verified|reviewed by|approved by a consultant/i);
  });

  it("names the service's own drafted output and its own computed output", () => {
    const seen = new Set<string>();
    for (const service of SERVICES) {
      const { unmount } = render(<HowAiWorks service={service} />);
      const text = disclosure().textContent ?? "";
      expect(text).toMatch(/What AI drafts here/);
      expect(text.length).toBeGreaterThan(400);
      seen.add(text);
      unmount();
    }
    // Every service gets its own pair of sentences; copy that said the same
    // thing four times would tell a consultant nothing about this service.
    expect(seen.size).toBe(SERVICES.length);
  });
});

const CLIENT_SURFACE_DIRS = ["../home", "../self-assessment"];
const CLIENT_SURFACE_FILES = ["../../app/home/page.tsx"];

function readRelative(rel: string): string {
  return readFileSync(fileURLToPath(new NodeUrl(rel, import.meta.url)), "utf8");
}

function clientSurfaceSources(): { path: string; source: string }[] {
  const out: { path: string; source: string }[] = [];
  for (const rel of CLIENT_SURFACE_FILES) {
    out.push({ path: rel, source: readRelative(rel) });
  }
  for (const dir of CLIENT_SURFACE_DIRS) {
    const dirPath = fileURLToPath(new NodeUrl(`${dir}/`, import.meta.url));
    for (const name of readdirSync(dirPath)) {
      if (!name.endsWith(".tsx") || name.endsWith(".test.tsx")) continue;
      out.push({
        path: `${dir}/${name}`,
        source: readFileSync(`${dirPath}${name}`, "utf8"),
      });
    }
  }
  return out;
}

/**
 * Drop comments so the guard reads only what can reach a client's screen. The
 * §6.4 notes in these files discuss AI on purpose; the rendered markup must
 * not. None of these files contain a "://" run, so line-comment stripping is
 * safe here.
 */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
}

const FORBIDDEN: [string, RegExp][] = [
  ["AI", /\bAI\b/],
  ["artificial intelligence", /artificial intelligence/i],
  ["LLM", /\bLLM\b/i],
  ["model output", /model output/i],
  ["Claude", /\bClaude\b/],
  ["Anthropic", /\bAnthropic\b/i],
  ["machine learning", /machine learning/i],
  ["drafted by", /drafted by/i],
];

describe("the client surface stays silent on AI", () => {
  it("finds the client-surface files it is supposed to be guarding", () => {
    const paths = clientSurfaceSources().map((f) => f.path);
    expect(paths).toContain("../../app/home/page.tsx");
    expect(paths).toContain("../home/HomeDashboard.tsx");
    expect(paths).toContain("../self-assessment/CsfSelfAssessment.tsx");
    expect(paths).toContain("../self-assessment/ZtSelfAssessment.tsx");
    expect(paths.length).toBeGreaterThanOrEqual(6);
  });

  it("renders no AI vocabulary in any client-surface component", () => {
    for (const { path, source } of clientSurfaceSources()) {
      const code = stripComments(source);
      for (const [label, pattern] of FORBIDDEN) {
        expect(
          pattern.test(code),
          `${path} mentions "${label}" outside a comment; the client surface must stay silent on AI (D-037)`,
        ).toBe(false);
      }
    }
  });

  it("keeps the section 6.4 AI-silent comment in home/page.tsx", () => {
    const normalized = readRelative("../../app/home/page.tsx")
      .replace(/\s*\n\s*\*\s*/g, " ")
      .replace(/\s+/g, " ");
    expect(normalized).toContain(
      "§6.4: this surface shows phase and next steps only, never scoring math, audit internals, or raw AI output.",
    );
  });
});
