/**
 * Marketing landing placeholder (stage 5 + stage 6 wiring).
 *
 * Renders a minimal version using @shield/design-system primitives so a real
 * `next build` exercises the design-system tokens + components. The full
 * Round-6 landing (hero, service cards, resource center, contact, footer)
 * lands in Phase 1 stage 7.
 */

import {
  Card,
  CardBody,
  CardDescription,
  CardHeader,
  CardTitle,
  StatusPill,
} from "@shield/design-system";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-6 py-16">
      <header className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-tertiary">
          SHIELD
        </p>
        <h1 className="text-4xl font-semibold leading-tight text-ink-primary sm:text-5xl">
          SHIELD by Kentro
        </h1>
        <p className="text-lg text-ink-secondary">
          Enterprise cybersecurity assessment platform. Technical Debt, Zero Trust, NIST CSF 2.0,
          MITRE ATT&amp;CK Coverage.
        </p>
      </header>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Phase 1 in progress</CardTitle>
            <StatusPill tone="info" withDot>
              Stage 6
            </StatusPill>
          </div>
          <CardDescription>
            The full marketing landing (hero, service cards, resource center) lands in Phase 1
            stage 7 per the Round 6 Design Contract. This page is a deliberate placeholder so the
            build can ship a typed, accessible shell before the visual layer arrives.
          </CardDescription>
        </CardHeader>
        <CardBody>
          <ul className="grid grid-cols-1 gap-3 text-sm text-ink-secondary sm:grid-cols-2">
            <li>Technical Debt Review</li>
            <li>Zero Trust Assessment (CISA + DoD)</li>
            <li>NIST CSF 2.0 Assessment</li>
            <li>MITRE ATT&amp;CK Coverage Mapping</li>
          </ul>
        </CardBody>
      </Card>
    </main>
  );
}
