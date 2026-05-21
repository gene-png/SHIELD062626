import { StatusPill } from "@shield/design-system";

import { Hero } from "@/components/marketing/Hero";
import { ServiceGrid } from "@/components/marketing/ServiceGrid";
import { PublicFooter } from "@/components/site/PublicFooter";
import { PublicHeader } from "@/components/site/PublicHeader";

export default function HomePage() {
  return (
    <>
      <PublicHeader />
      <Hero />
      <ServiceGrid />
      <section
        aria-labelledby="trust-heading"
        className="border-t border-border-subtle bg-surface-card"
      >
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-wrap items-center gap-3">
            <StatusPill tone="info" withDot>
              FedRAMP-targeted
            </StatusPill>
            <StatusPill tone="success" withDot>
              WCAG 2.1 AA
            </StatusPill>
          </div>
          <h2
            id="trust-heading"
            className="mt-4 text-xl font-semibold text-ink-primary"
          >
            Built for federal mission systems
          </h2>
          <p className="mt-2 max-w-2xl text-ink-secondary">
            Mandatory PII redaction on every AI call, append-only audit log,
            short-lived JWT sessions with account lockout, and self-hosted
            infrastructure — no third-party CDNs.
          </p>
        </div>
      </section>
      <PublicFooter />
    </>
  );
}
