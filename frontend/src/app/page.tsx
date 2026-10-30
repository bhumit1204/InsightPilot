export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center gap-4 px-4 py-24 sm:px-6">
      <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
        See what is in your data, what changed, and why.
      </h1>
      <p className="max-w-prose text-lg text-ink-muted">
        Upload a CSV of sales, expenses or staff records. The upload screen arrives in the next
        step.
      </p>
    </main>
  );
}
