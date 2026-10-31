"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useDeleteSession } from "@/lib/api/hooks";

export function DeleteSessionButton({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const remove = useDeleteSession();
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
        Delete this data
      </Button>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Confirm delete">
      <span className="text-sm text-ink-muted">Delete the file and all results?</span>
      <Button
        variant="danger"
        size="sm"
        disabled={remove.isPending}
        onClick={() => remove.mutate(sessionId, { onSuccess: () => router.push("/") })}
      >
        {remove.isPending ? "Deleting…" : "Delete"}
      </Button>
      <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
        Keep it
      </Button>
      {remove.isError && (
        <span role="alert" className="text-sm text-danger">
          {remove.error.message}
        </span>
      )}
    </div>
  );
}
