"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSamples, useStartFromSample } from "@/lib/api/hooks";
import { formatBytes, plural } from "@/lib/format";

export function SampleList() {
  const router = useRouter();
  const samples = useSamples();
  const start = useStartFromSample();
  const [openingKey, setOpeningKey] = useState<string | null>(null);

  function open(key: string) {
    setOpeningKey(key);
    start.mutate(key, {
      onSuccess: (session) => {
        router.push(`/sessions/${session.session_id}`);
        start.reset();
        setOpeningKey(null);
      },
      onError: () => setOpeningKey(null),
    });
  }

  if (samples.isPending) {
    return (
      <div className="flex flex-col gap-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
    );
  }

  if (samples.isError) {
    return (
      <p className="text-ink-muted">
        Sample datasets load from the server, which can&apos;t be reached right now.
      </p>
    );
  }

  if (samples.data.length === 0) {
    return (
      <p className="text-ink-muted">
        No sample datasets on this server. Run <code>python samples/generate_samples.py</code>{" "}
        from the project folder to create them.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <ul className="divide-y divide-rule border-y border-rule">
        {samples.data.map((sample) => (
          <li
            key={sample.key}
            className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-8"
          >
            <div className="flex max-w-prose flex-col gap-1">
              <p className="font-bold">{sample.title}</p>
              <p className="text-ink-muted">{sample.description}</p>
              <p className="text-sm text-ink-muted">
                {plural(sample.rows, "row")}, {plural(sample.columns, "column")},{" "}
                {formatBytes(sample.size_bytes)}
              </p>
            </div>
            <Button
              variant="secondary"
              className="self-start sm:self-center"
              disabled={openingKey !== null}
              onClick={() => open(sample.key)}
            >
              {openingKey === sample.key ? "Opening…" : "Open this sample"}
            </Button>
          </li>
        ))}
      </ul>
      {start.isError && (
        <p role="alert" className="text-sm text-danger">
          {start.error.message}
        </p>
      )}
    </div>
  );
}
