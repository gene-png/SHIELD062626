import Link from "next/link";

export function Hero(): JSX.Element {
  return (
    <section className="border-b border-border-subtle bg-surface-card">
      <div className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">
          Federal-grade cybersecurity engagements
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-ink-primary sm:text-5xl">
          One platform for technical debt, zero trust, NIST&nbsp;CSF&nbsp;2.0, and ATT&amp;CK
          coverage.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-ink-secondary">
          SHIELD by Kentro replaces ad-hoc spreadsheets and slide decks with a guided assessment
          workspace that meets your auditors where they live. Single-tenant per engagement,
          FedRAMP-targeted, accessibility-first.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            href="/sign-up"
            className="rounded-md bg-brand-500 px-5 py-3 text-sm font-semibold text-ink-on-accent hover:bg-brand-600"
          >
            Start an engagement
          </Link>
          <Link
            href="/sign-in"
            className="rounded-md border border-border bg-surface-card px-5 py-3 text-sm font-semibold text-ink-primary hover:bg-surface-sunken"
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}
