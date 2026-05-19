/**
 * Marketing landing placeholder.
 *
 * Stage 5 ships a minimal page so the Next.js skeleton has something to
 * render under `next build`. The real Round-6 landing (hero, service
 * cards, resource center, contact, footer) lands in stage 7.
 */

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.18em] text-ink-400">SHIELD</p>
        <h1 className="text-4xl font-semibold leading-tight text-ink-900 sm:text-5xl">
          SHIELD by Kentro
        </h1>
        <p className="text-lg text-ink-600">
          Enterprise cybersecurity assessment platform. Technical Debt, Zero Trust, NIST CSF 2.0,
          MITRE ATT&amp;CK Coverage.
        </p>
      </header>
      <section className="rounded-xl border border-ink-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-ink-600">
          The full marketing landing (hero, service cards, resource center) lands in Phase 1 stage 7
          per the Round 6 Design Contract. This page is a deliberate placeholder so the build can
          ship a typed, accessible shell before the visual layer arrives.
        </p>
      </section>
    </main>
  );
}
