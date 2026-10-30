import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

/** A grey placeholder shown while data loads. */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-md bg-terrain", className)}
      {...props}
    />
  );
}