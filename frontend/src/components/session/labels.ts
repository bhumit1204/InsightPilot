import type { ColumnProfile } from "@/lib/api/client";

type Tone = "neutral" | "info" | "highlight" | "ok" | "caution" | "danger";

export const TYPE_LABELS: Record<ColumnProfile["type"], string> = {
  numeric: "Number",
  datetime: "Date",
  boolean: "Yes / no",
  text: "Text",
};

export const ROLE_LABELS: Record<ColumnProfile["role"], { label: string; hint: string; tone: Tone }> =
  {
    time: { label: "Time", hint: "Used to show trends over time", tone: "info" },
    metric: { label: "Measure", hint: "A number worth adding up or averaging", tone: "ok" },
    category: { label: "Category", hint: "Groups the data, like region or product", tone: "neutral" },
    identifier: { label: "ID", hint: "Unique per row; left out of charts", tone: "neutral" },
    free_text: { label: "Free text", hint: "Long, varied text; not analysed yet", tone: "neutral" },
    ignored: { label: "Left out", hint: "Same value in every row, so it tells nothing", tone: "neutral" },
  };
