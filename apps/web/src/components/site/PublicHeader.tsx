import Link from "next/link";

export function PublicHeader(): JSX.Element {
  return (
    <header className="border-b border-border-subtle bg-surface-card">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex flex-col leading-tight">
          <span className="text-lg font-semibold tracking-tight text-ink-primary">SHIELD</span>
          <span className="text-xs font-medium uppercase tracking-wider text-ink-tertiary">
            by Kentro
          </span>
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-4 text-sm">
          <Link
            href="/sign-in"
            className="rounded-md px-3 py-2 font-medium text-ink-secondary hover:text-ink-primary"
          >
            Sign in
          </Link>
          <Link
            href="/sign-up"
            className="rounded-md bg-brand-500 px-3 py-2 font-semibold text-ink-on-accent hover:bg-brand-600"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
