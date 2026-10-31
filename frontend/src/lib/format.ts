// Indian digit grouping (1,23,456) matches how the target users read numbers.
const numberFormat = new Intl.NumberFormat("en-IN");

export function formatNumber(value: number): string {
  return numberFormat.format(value);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function plural(count: number, word: string, pluralWord = `${word}s`): string {
  return `${formatNumber(count)} ${count === 1 ? word : pluralWord}`;
}

const dateFormat = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC", // dates from the data have no time zone; show them as written
});

/** "2019-01-01" or "2019-01-01T00:00:00" -> "1 Jan 2019". */
export function formatDate(value: string): string {
  const date = new Date(value.length === 10 ? `${value}T00:00:00Z` : `${value.replace(/Z$/, "")}Z`);
  return Number.isNaN(date.getTime()) ? value : dateFormat.format(date);
}

/** Compact numbers for summaries: 1,23,456.78 stays exact, long decimals are trimmed. */
export function formatValue(value: number): string {
  const rounded = Math.abs(value) >= 100 ? Math.round(value) : Math.round(value * 100) / 100;
  return formatNumber(rounded);
}

export function formatPercent(value: number): string {
  if (value === 0) return "0%";
  if (value < 0.1) return "under 0.1%";
  return `${value < 10 ? value.toFixed(1) : Math.round(value)}%`;
}
