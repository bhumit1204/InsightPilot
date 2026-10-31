/**
 * Turn raw data vocabulary into plain words: column names, record nouns, money amounts.
 * The target reader runs a business, not a database, so "revenue_inr" becomes "Revenue (INR)".
 */
import { formatNumber } from "./format";

const UNITS: Record<string, string> = {
  inr: "INR",
  usd: "USD",
  gbp: "GBP",
  eur: "EUR",
  aed: "AED",
  sgd: "SGD",
  pct: "%",
  percent: "%",
};

function words(name: string): string[] {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .split(/[_\s\-.]+/)
    .filter(Boolean)
    .map((w) => w.toLowerCase());
}

/** "revenue_inr" -> "Revenue (INR)", "order_line_id" -> "Order line ID", "hireDate" -> "Hire date". */
export function humanizeColumn(name: string): string {
  const parts = words(name);
  let unit: string | undefined;
  const last = parts.at(-1);
  if (parts.length > 1 && last && UNITS[last]) {
    unit = UNITS[last];
    parts.pop();
  }
  const label = parts.map((w) => (w === "id" ? "ID" : w)).join(" ");
  const capitalised = label.charAt(0).toUpperCase() + label.slice(1);
  return unit ? `${capitalised} (${unit})` : capitalised;
}

/** Lower-case plural for use inside a sentence: "region" -> "regions", "city" -> "cities". */
export function pluralColumn(name: string, count: number): string {
  const parts = words(name).filter((w) => !UNITS[w]);
  const noun = parts.join(" ") || name;
  if (count === 1) return noun;
  if (/[^aeiou]y$/.test(noun)) return `${noun.slice(0, -1)}ies`;
  if (/(s|x|ch|sh)$/.test(noun)) return `${noun}es`;
  return `${noun}s`;
}

const RECORD_NOUNS: Record<string, [string, string]> = {
  retail_sales: ["sales record", "sales records"],
  hr: ["employee record", "employee records"],
  expenses: ["expense entry", "expense entries"],
  finance: ["transaction", "transactions"],
  marketing: ["campaign record", "campaign records"],
  saas: ["account record", "account records"],
  inventory: ["stock record", "stock records"],
};

export function recordNoun(domain: string, count: number): string {
  const [one, many] = RECORD_NOUNS[domain] ?? ["row", "rows"];
  return count === 1 ? one : many;
}

/** Measures where adding values up means nothing: an average describes them better. */
const AVERAGE_WORDS = ["price", "rate", "salary", "age", "rating", "score", "percent", "pct", "margin", "discount", "tenure"];

export function prefersAverage(column: string): boolean {
  const parts = words(column);
  return parts.some((w) => AVERAGE_WORDS.includes(w));
}

const SYMBOLS: Record<string, string> = { INR: "₹", USD: "$", GBP: "£", EUR: "€", SGD: "S$" };

/** Money in the units people say out loud: ₹51.2 crore, ₹9.6 lakh, $1.2M. */
export function formatMoney(value: number, currency: string | null | undefined): string {
  const symbol = currency ? (SYMBOLS[currency] ?? `${currency} `) : "";
  if (currency === "INR") {
    const abs = Math.abs(value);
    if (abs >= 1e7) return `${symbol}${trim(value / 1e7)} crore`;
    if (abs >= 1e5) return `${symbol}${trim(value / 1e5)} lakh`;
    return `${symbol}${formatNumber(Math.round(value))}`;
  }
  const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
  return `${symbol}${compact.format(value)}`;
}

function trim(value: number): string {
  return value >= 100 ? formatNumber(Math.round(value)) : String(Math.round(value * 10) / 10);
}
