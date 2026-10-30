export function SiteFooter() {
  return (
    <footer className="border-t border-rule">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-sm text-ink-muted sm:px-6">
        <p>Numbers come from your data, computed exactly. Nothing is estimated.</p>
        <a
          href="https://github.com/bhumit1204/InsightPilot"
          className="rounded underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
        >
          Source code on GitHub
        </a>
      </div>
    </footer>
  );
}