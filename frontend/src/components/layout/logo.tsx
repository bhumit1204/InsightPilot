import Link from "next/link";

/**
 * The mark is a VOR navigation beacon from aeronautical charts: a hexagon with a centre
 * point, the symbol pilots steer by. It matches the chart-inspired palette.
 */
export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5 rounded-md text-ink">
      <svg viewBox="0 0 32 32" aria-hidden className="size-7 text-chart-blue">
        <polygon
          points="16,3 27.3,9.5 27.3,22.5 16,29 4.7,22.5 4.7,9.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
        <circle cx="16" cy="16" r="3.5" className="fill-route" />
      </svg>
      <span className="text-lg font-bold tracking-tight">InsightPilot</span>
    </Link>
  );
}