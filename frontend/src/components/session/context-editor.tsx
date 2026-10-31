"use client";

import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import type { ContextResponse } from "@/lib/api/client";
import { useConfirmContext } from "@/lib/api/hooks";
import { humanizeColumn } from "@/lib/humanize";

const selectClass =
  "h-10 w-full rounded-md border border-rule bg-surface px-3 text-ink disabled:opacity-50";

/** A small form for correcting what the data is about. Only shown when asked, or when unsure. */
export function ContextEditor({
  sessionId,
  data,
  prompt,
  onDone,
}: {
  sessionId: string;
  data: ContextResponse;
  prompt?: string;
  onDone: () => void;
}) {
  const { context, options } = data;
  const confirm = useConfirmContext(sessionId);
  const [domain, setDomain] = useState(context.domain);
  const [region, setRegion] = useState(context.region);
  const [metric, setMetric] = useState(context.primary_metric ?? "");
  const [grain, setGrain] = useState(context.time_grain ?? "");

  function save(event: FormEvent) {
    event.preventDefault();
    confirm.mutate(
      {
        domain,
        region,
        primary_metric: metric || null,
        time_grain: grain || null,
      },
      { onSuccess: onDone },
    );
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-4 rounded-lg border border-rule bg-surface p-5">
      {prompt && <p className="font-semibold">{prompt}</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-muted">What is this data about?</span>
          <select className={selectClass} value={domain} onChange={(e) => setDomain(e.target.value)}>
            {options.domains.map((d) => (
              <option key={d.key} value={d.key}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-muted">Where is it from?</span>
          <select className={selectClass} value={region} onChange={(e) => setRegion(e.target.value)}>
            {options.regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-muted">Main number to track</span>
          <select
            className={selectClass}
            value={metric}
            disabled={options.metrics.length === 0}
            onChange={(e) => setMetric(e.target.value)}
          >
            {options.metrics.length === 0 && <option value="">No number columns</option>}
            {options.metrics.map((m) => (
              <option key={m} value={m}>
                {humanizeColumn(m)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-ink-muted">Show trends by</span>
          <select
            className={selectClass}
            value={grain}
            disabled={options.time_columns.length === 0}
            onChange={(e) => setGrain(e.target.value)}
          >
            {options.time_columns.length === 0 && <option value="">No date column</option>}
            {options.time_grains.map((g) => (
              <option key={g} value={g}>
                {g.charAt(0).toUpperCase() + g.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="submit" disabled={confirm.isPending}>
          {confirm.isPending ? "Saving…" : "Save"}
        </Button>
        <Button variant="ghost" onClick={onDone} disabled={confirm.isPending}>
          Cancel
        </Button>
        {confirm.isError && (
          <span role="alert" className="text-sm text-danger">
            {confirm.error.message}
          </span>
        )}
      </div>
    </form>
  );
}
