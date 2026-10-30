import { BackendStatus } from "@/components/backend-status";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-4 px-6 py-24">
      <h1 className="text-4xl font-bold tracking-tight">InsightPilot</h1>
      <p className="max-w-prose text-lg text-ink-muted">
        Upload a CSV and see what is in your data, what changed, and why. The upload screen
        arrives in the next steps of Phase 4.
      </p>
      <BackendStatus />
    </main>
  );
}