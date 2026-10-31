"use client";

import { Badge } from "@/components/ui/badge";
import type { ColumnProfile } from "@/lib/api/client";
import { useApplyFix } from "@/lib/api/hooks";
import { cn } from "@/lib/cn";
import { formatDate, formatNumber, formatPercent, formatValue } from "@/lib/format";
import { humanizeColumn } from "@/lib/humanize";

import { ROLE_LABELS, TYPE_LABELS } from "./labels";

function summary(column: ColumnProfile): string {
  const { stats } = column;
  if (column.role === "identifier") return `${formatNumber(stats.unique)} distinct values`;
  if (column.type === "numeric" && typeof stats.min === "number" && typeof stats.max === "number") {
    const median = stats.median != null ? `, median ${formatValue(stats.median)}` : "";
    return `${formatValue(stats.min)} to ${formatValue(stats.max)}${median}`;
  }
  if (column.type === "datetime" && typeof stats.min === "string" && typeof stats.max === "string") {
    return `${formatDate(stats.min)} to ${formatDate(stats.max)}`;
  }
  if (stats.top_values?.length) {
    const top = stats.top_values.slice(0, 3).map((v) => v.value).join(", ");
    const more = stats.unique > 3 ? ` and ${formatNumber(stats.unique - 3)} more` : "";
    return `${top}${more}`;
  }
  return `${formatNumber(stats.unique)} distinct values`;
}

function TypeSelect({ sessionId, column }: { sessionId: string; column: ColumnProfile }) {
  const applyFix = useApplyFix(sessionId);
  return (
    <div className="flex flex-col gap-1">
      <select
        aria-label={`Type of ${column.name}`}
        value={column.type}
        disabled={applyFix.isPending}
        onChange={(event) =>
          applyFix.mutate({
            action: "set_type",
            column: column.name,
            type: event.target.value as ColumnProfile["type"],
          })
        }
        className="h-8 rounded-md border border-rule bg-surface px-2 text-sm text-ink disabled:opacity-50"
      >
        {Object.entries(TYPE_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      {applyFix.isError && (
        <span role="alert" className="max-w-48 text-xs text-danger">
          {applyFix.error.message}
        </span>
      )}
    </div>
  );
}

function MissingBar({ pct }: { pct: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-terrain" aria-hidden>
        <div
          className={cn("h-full rounded-full", pct >= 20 ? "bg-caution" : "bg-ink-muted/60")}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <span className={cn("text-sm", pct >= 20 && "font-semibold text-caution")}>
        {formatPercent(pct)}
      </span>
    </div>
  );
}

export function ColumnTable({ sessionId, columns }: { sessionId: string; columns: ColumnProfile[] }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto border-y border-rule">
        <table className="w-full min-w-[760px] text-left">
          <thead className="text-sm text-ink-muted">
            <tr className="border-b border-rule">
              <th scope="col" className="py-2 pr-4 font-semibold">Column</th>
              <th scope="col" className="py-2 pr-4 font-semibold">Type</th>
              <th scope="col" className="py-2 pr-4 font-semibold">Used as</th>
              <th scope="col" className="py-2 pr-4 font-semibold">Empty</th>
              <th scope="col" className="py-2 font-semibold">Values</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {columns.map((column) => {
              const role = ROLE_LABELS[column.role];
              return (
                <tr key={column.name} className="align-top">
                  <th scope="row" className="py-3 pr-4 font-semibold">
                    <div className="flex flex-col gap-1">
                      <span>{humanizeColumn(column.name)}</span>
                      {humanizeColumn(column.name).toLowerCase() !== column.name.toLowerCase() && (
                        <span className="text-xs font-normal break-all text-ink-muted">{column.name}</span>
                      )}
                      <span className="flex flex-wrap gap-1">
                        {column.details.currency && <Badge>Currency</Badge>}
                        {column.details.percent && <Badge>Percent</Badge>}
                        {column.details.overridden && <Badge tone="info">Set by you</Badge>}
                      </span>
                    </div>
                  </th>
                  <td className="py-3 pr-4">
                    <TypeSelect sessionId={sessionId} column={column} />
                  </td>
                  <td className="py-3 pr-4">
                    <Badge tone={role.tone} title={role.hint}>
                      {role.label}
                    </Badge>
                  </td>
                  <td className="py-3 pr-4">
                    <MissingBar pct={column.stats.missing_pct} />
                  </td>
                  <td className="py-3 text-ink-muted">{summary(column)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
