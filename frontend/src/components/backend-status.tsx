"use client";

import { API_URL } from "@/lib/api/client";
import { useHealth } from "@/lib/api/hooks";

/** A small connection check: proves the frontend can reach the backend. */
export function BackendStatus() {
  const { isPending, isError, error } = useHealth();

  if (isPending) return <p className="text-sm text-ink-muted">Checking the server…</p>;

  if (isError) {
    return (
      <p role="alert" className="text-sm text-danger">
        {error.message}
      </p>
    );
  }

  return (
    <p className="flex items-center gap-2 text-sm text-ink-muted">
      <span aria-hidden className="size-2 rounded-full bg-ok" />
      Connected to the server at {API_URL}
    </p>
  );
}