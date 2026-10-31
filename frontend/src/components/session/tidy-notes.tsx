"use client";

import { Check, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CleanRequest, Profile } from "@/lib/api/client";
import { useApplyFix, useCleanLog, useResetCleaning } from "@/lib/api/hooks";
import { formatDate, formatPercent, plural } from "@/lib/format";
import { humanizeColumn } from "@/lib/humanize";

type Note = {
  key: string;
  kind: "done" | "info";
  text: string;
  action?: { label: string; request: CleanRequest };
};

const MOSTLY_EMPTY_PCT = 50;

function describeFix(fix: Record<string, unknown>): string {
  const column = typeof fix.column === "string" ? humanizeColumn(fix.column) : "";
  const removed = Number(fix.rows_before) - Number(fix.rows_after);
  switch (fix.action) {
    case "drop_duplicates":
      return `Removed ${plural(removed, "row")} that ${removed === 1 ? "was an exact copy" : "were exact copies"} of another row.`;
    case "drop_missing_rows":
      return `Removed ${plural(removed, "row")} where ${column} was empty.`;
    case "fill_missing":
      return `Filled ${plural(Number(fix.cells), "empty cell")} in ${column} with ${String(fix.value)}.`;
    case "drop_column":
      return `Removed the ${column} column.`;
    case "set_type": {
      if (fix.type === "datetime" && typeof fix.date_format === "string") {
        const order = fix.date_format.startsWith("%m") ? "month first (MM/DD)" : "day first (DD/MM)";
        return `Reading dates in ${column} as ${order}.`;
      }
      const kind = { numeric: "numbers", datetime: "dates", boolean: "yes / no", text: "text" }[
        String(fix.type)
      ];
      return `Reading ${column} as ${kind ?? String(fix.type)}.`;
    }
    default:
      return String(fix.action);
  }
}

/** Plain-language notes from the profile: only what a person might care about. */
function notesFromProfile(profile: Profile): Note[] {
  const columns = new Map(profile.column_details.map((c) => [c.name, c]));
  const notes: Note[] = [];

  for (const warning of profile.warnings) {
    const name = warning.column ?? "";
    const label = humanizeColumn(name);
    const column = columns.get(name);

    switch (warning.code) {
      case "DUPLICATE_ROWS":
        notes.push({
          key: warning.code,
          kind: "info",
          text: `${plural(profile.duplicate_rows, "row")} ${profile.duplicate_rows === 1 ? "is an exact copy" : "are exact copies"} of another row.`,
          action: { label: "Remove copies", request: { action: "drop_duplicates" } },
        });
        break;
      case "AMBIGUOUS_DATES": {
        const dayFirst = column?.details.format ?? "%d/%m/%Y";
        const monthFirst = dayFirst
          .replace("%d", "%MONTH%")
          .replace("%m", "%d")
          .replace("%MONTH%", "%m");
        notes.push({
          key: `${warning.code}-${name}`,
          kind: "done",
          text: `Reading dates in ${label} as day first (DD/MM), for example 03/04 as 3 April.`,
          action: {
            label: "Use month first",
            request: { action: "set_type", column: name, type: "datetime", date_format: monthFirst },
          },
        });
        break;
      }
      case "CONSTANT_COLUMN":
        notes.push({
          key: `${warning.code}-${name}`,
          kind: "done",
          text: `Leaving out ${label}: every row has the same value.`,
        });
        break;
      case "HIGH_MISSING":
        if (column && column.stats.missing_pct >= MOSTLY_EMPTY_PCT) {
          notes.push({
            key: `${warning.code}-${name}`,
            kind: "info",
            text: `${label} is mostly empty (${formatPercent(column.stats.missing_pct)}). Empty cells are skipped in calculations.`,
          });
        }
        break;
      case "CONVERSION_LOSS":
        notes.push({
          key: `${warning.code}-${name}`,
          kind: "info",
          text: `Some values in ${label} could not be read and are skipped.`,
          action: {
            label: "Treat as text",
            request: { action: "set_type", column: name, type: "text" },
          },
        });
        break;
      case "TIME_GAPS": {
        const gaps = profile.time?.gaps ?? [];
        const listed = gaps
          .slice(0, 3)
          .map((g) => (g.start === g.end ? formatDate(g.start) : `${formatDate(g.start)} to ${formatDate(g.end)}`));
        if (listed.length) {
          notes.push({
            key: warning.code,
            kind: "info",
            text: `No data for ${listed.join("; ")}${gaps.length > 3 ? ` and ${gaps.length - 3} more gaps` : ""}.`,
          });
        }
        break;
      }
    }
  }
  return notes;
}

/** "We checked your data": what was fixed automatically, and anything worth knowing. */
export function TidyNotes({ sessionId, profile }: { sessionId: string; profile: Profile }) {
  const log = useCleanLog(sessionId);
  const reset = useResetCleaning(sessionId);
  const applyFix = useApplyFix(sessionId);

  const fixes = log.data?.fixes ?? [];
  const notes: Note[] = [
    ...fixes.map((fix, i) => ({ key: `fix-${i}`, kind: "done" as const, text: describeFix(fix) })),
    ...notesFromProfile(profile),
  ];
  const error = reset.error ?? applyFix.error;

  return (
    <section aria-labelledby="checked-heading" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="checked-heading" className="text-lg font-bold">
          We checked your data
        </h2>
        {fixes.length > 0 && (
          <Button size="sm" variant="ghost" disabled={reset.isPending} onClick={() => reset.mutate()}>
            {reset.isPending ? "Undoing…" : "Undo changes"}
          </Button>
        )}
      </div>

      {notes.length === 0 ? (
        <p className="flex items-center gap-2 text-ink-muted">
          <Check aria-hidden className="size-4 text-ok" />
          Everything read cleanly. Nothing needed fixing.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {notes.map((note) => (
            <li key={note.key} className="flex flex-wrap items-start gap-x-3 gap-y-1">
              {note.kind === "done" ? (
                <Check aria-hidden className="mt-1 size-4 shrink-0 text-ok" />
              ) : (
                <Info aria-hidden className="mt-1 size-4 shrink-0 text-chart-blue" />
              )}
              <span className="max-w-prose flex-1 text-ink-muted">{note.text}</span>
              {note.action && (
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={applyFix.isPending}
                  onClick={() => applyFix.mutate(note.action!.request)}
                >
                  {note.action.label}
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <p role="alert" className="text-sm text-danger">
          {error.message}
        </p>
      )}
    </section>
  );
}
