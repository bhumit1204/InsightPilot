import { DropZone } from "@/components/upload/drop-zone";
import { SampleList } from "@/components/upload/sample-list";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-14 px-4 py-12 sm:px-6 sm:py-16">
      <section className="flex flex-col gap-8">
        <div className="flex flex-col gap-4">
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-balance sm:text-5xl">
            See what is in your data, what changed, and why.
          </h1>
          <p className="max-w-2xl text-lg text-ink-muted">
            Upload a CSV of sales, expenses or staff records. InsightPilot reads it, tidies it up
            and tells you what it holds in plain words. No setup, no formulas.
          </p>
        </div>
        <DropZone />
        <p className="max-w-2xl text-sm text-ink-muted">
          Your file is stored only for this analysis, and you can delete it at any time. Its
          rows are never sent to an AI service.
        </p>
      </section>

      <section aria-labelledby="samples-heading" className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 id="samples-heading" className="text-2xl font-bold tracking-tight">
            No file handy? Try sample data
          </h2>
          <p className="max-w-2xl text-ink-muted">
            Each sample hides real patterns to find, from the 2020 lockdown to festival rushes.
          </p>
        </div>
        <SampleList />
      </section>
    </main>
  );
}
