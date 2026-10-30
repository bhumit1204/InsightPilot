import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-terrain text-ink",
        info: "bg-chart-blue/12 text-chart-blue",
        highlight: "bg-route/12 text-route",
        ok: "bg-ok/12 text-ok",
        caution: "bg-caution/15 text-caution",
        danger: "bg-danger/12 text-danger",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>;

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}