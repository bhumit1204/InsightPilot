"use client";

import { API_URL } from "@/lib/api/client";
import { useHealth } from "@/lib/api/hooks";
import { cn } from "@/lib/cn";

/** Header indicator: can the frontend reach the backend right now? */
export function BackendStatus() {
  const { isPending, isError, error } = useHealth();

  const state = isPending ? "checking" : isError ? "offline" : "online";
  const label = { checking: "Checking server", offline: "Server offline", online: "Server connected" }[
    state
  ];
  const detail = isError ? error.message : `Backend at ${API_URL}`;

  return (
    <p
      role={state === "offline" ? "alert" : "status"}
      title={detail}
      className="flex items-center gap-2 text-sm text-ink-muted"
    >
      <span
        aria-hidden
        className={cn(
          "size-2 rounded-full",
          state === "online" && "bg-ok",
          state === "offline" && "bg-danger",
          state === "checking" && "animate-pulse bg-rule",
        )}
      />
      <span className={cn(state === "offline" && "text-danger")}>{label}</span>
      <span className="sr-only">. {detail}</span>
    </p>
  );
}
