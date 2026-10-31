import type { ColumnProfile, DataContext, Profile } from "@/lib/api/client";
import { formatNumber, formatValue } from "@/lib/format";
import { formatMoney, humanizeColumn, pluralColumn, prefersAverage, recordNoun } from "@/lib/humanize";

const monthYear = new Intl.DateTimeFormat("en-IN", { month: "short", year: "numeric", timeZone: "UTC" });

function month(value: string): string {
  const date = new Date(value.length === 10 ? `${value}T00:00:00Z` : `${value.replace(/Z$/, "")}Z`);
  return Number.isNaN(date.getTime()) ? value : monthYear.format(date);
}

/** Up to two category columns that make a good "across 4 regions and 6 products" phrase. */
function groupings(profile: Profile): ColumnProfile[] {
  return profile.column_details
    .filter((c) => c.role === "category" && c.stats.unique >= 2 && c.stats.unique <= 50)
    // The most varied groupings say the most: "6 products and 4 regions", not "2 statuses".
    .sort((a, b) => b.stats.unique - a.stats.unique)
    .slice(0, 2);
}

export function storyTitle(context: DataContext | undefined): string {
  if (!context || context.domain === "general") return "Your data";
  return context.region && context.region !== "Global"
    ? `${context.domain_label}, ${context.region}`
    : context.domain_label;
}

/** One plain sentence describing what the file holds. */
export function storySentence(profile: Profile, context: DataContext | undefined): string {
  const count = profile.rows;
  let sentence = `${formatNumber(count)} ${recordNoun(context?.domain ?? "general", count)}`;

  const time = profile.time;
  if (time?.start && time.end) {
    const start = month(time.start);
    const end = month(time.end);
    sentence += start === end ? ` from ${start}` : ` from ${start} to ${end}`;
  }

  const groups = groupings(profile).map((c) =>
    // A cryptic name like "b" reads badly as "2 bs"; say "2 values of B" instead.
    c.name.length < 3
      ? `${formatNumber(c.stats.unique)} values of ${humanizeColumn(c.name)}`
      : `${formatNumber(c.stats.unique)} ${pluralColumn(c.name, c.stats.unique)}`,
  );
  if (groups.length) sentence += `, across ${groups.join(" and ")}`;
  return `${sentence}.`;
}

/** The headline number for the main measure: a total, or an average where totals mean nothing. */
export function keyFigure(profile: Profile, context: DataContext | undefined): string | null {
  const name = context?.primary_metric;
  const column = profile.column_details.find((c) => c.name === name);
  if (!column) return null;
  const label = humanizeColumn(column.name);
  const isMoney = Boolean(column.details.currency) || /\((INR|USD|GBP|EUR|AED|SGD)\)$/.test(label);
  const currency = isMoney ? (context?.currency ?? null) : null;
  const show = (v: number) => (isMoney ? formatMoney(v, currency) : formatValue(v));

  if (prefersAverage(column.name) && column.stats.mean != null) {
    return `${label} averages ${show(column.stats.mean)}.`;
  }
  if (column.stats.sum != null) return `${label} adds up to ${show(column.stats.sum)}.`;
  return null;
}
