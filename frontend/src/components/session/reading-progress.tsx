import { Check, LoaderCircle } from "lucide-react";

import { cn } from "@/lib/cn";

type Step = { label: string; done: boolean };

/** Shown while the first results load: real steps that tick off as each answer arrives. */
export function ReadingProgress({ steps }: { steps: Step[] }) {
  const current = steps.findIndex((s) => !s.done);
  return (
    <div className="flex flex-col gap-5 py-10" aria-live="polite" aria-busy="true">
      <h1 className="text-3xl font-bold tracking-tight">Reading your data</h1>
      <ol className="flex flex-col gap-3">
        {steps.map((step, i) => (
          <li
            key={step.label}
            className={cn(
              "flex items-center gap-3 text-lg",
              step.done ? "text-ink" : i === current ? "text-ink" : "text-ink-muted/60",
            )}
          >
            {step.done ? (
              <Check aria-hidden className="size-5 text-ok" />
            ) : i === current ? (
              <LoaderCircle aria-hidden className="size-5 animate-spin text-chart-blue" />
            ) : (
              <span aria-hidden className="size-5 rounded-full border-2 border-rule" />
            )}
            {step.label}
            <span className="sr-only">{step.done ? " (done)" : i === current ? " (in progress)" : ""}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
