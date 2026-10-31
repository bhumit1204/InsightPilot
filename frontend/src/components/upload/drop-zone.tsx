"use client";

import { FileUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { type DragEvent, useId, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { MAX_UPLOAD_MB } from "@/lib/api/client";
import { useUploadCsv } from "@/lib/api/hooks";
import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";

function checkFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    return `"${file.name}" is not a CSV file. In Excel, use File > Save As > CSV, then try again.`;
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `"${file.name}" is ${formatBytes(file.size)}. The limit is ${MAX_UPLOAD_MB} MB.`;
  }
  if (file.size === 0) return `"${file.name}" is empty.`;
  return null;
}

/**
 * The upload area, drawn as a sheet of chart paper. Drop a CSV or pick one with the button;
 * progress shows as a route line crossing the sheet.
 */
export function DropZone() {
  const router = useRouter();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const upload = useUploadCsv();

  const busy = upload.isPending;
  const error = fileError ?? upload.error?.message ?? null;

  function start(file: File) {
    const problem = checkFile(file);
    setFileError(problem);
    if (problem) return;
    setFileName(file.name);
    upload.mutate(file, {
      onSuccess: (session) => {
        router.push(`/sessions/${session.session_id}`);
        // Pages stay mounted in the background; reset so going back shows a fresh zone.
        upload.reset();
        setFileName(null);
      },
    });
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    if (busy) return;
    const files = event.dataTransfer.files;
    if (files.length > 1) {
      setFileError("Drop one file at a time.");
      return;
    }
    if (files[0]) start(files[0]);
  }

  const percent = Math.round(upload.progress * 100);
  const status = !busy
    ? null
    : upload.progress < 1
      ? `Uploading ${fileName}: ${percent}%`
      : `Reading ${fileName}: checking encoding, separators and columns`;

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "chart-paper relative flex min-h-72 flex-col items-center justify-center gap-5 overflow-hidden rounded-lg border-2 border-dashed px-6 py-12 text-center transition-colors",
          dragging ? "border-chart-blue bg-chart-blue/5" : "border-rule bg-surface",
          error && !busy && "border-danger/60",
        )}
      >
        <FileUp aria-hidden className={cn("size-10", dragging ? "text-chart-blue" : "text-ink-muted")} />

        {busy ? (
          <div className="flex w-full max-w-md flex-col gap-3" aria-live="polite">
            <p className="font-semibold">{status}</p>
            <div
              role="progressbar"
              aria-label="Upload progress"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={percent}
              className="relative h-1.5 w-full rounded-full bg-terrain"
            >
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-route transition-[width] duration-200"
                style={{ width: `${Math.max(percent, 2)}%` }}
              />
              <div
                aria-hidden
                className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface bg-route transition-[left] duration-200"
                style={{ left: `${Math.max(percent, 2)}%` }}
              />
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <p className="text-xl font-bold">
                {dragging ? "Drop to start the analysis" : "Drop a CSV file here"}
              </p>
              <p className="text-ink-muted">Up to {MAX_UPLOAD_MB} MB. The first row should hold column names.</p>
            </div>
            <Button size="lg" onClick={() => inputRef.current?.click()}>
              Choose a CSV file
            </Button>
          </>
        )}

        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          tabIndex={-1}
          aria-label="Choose a CSV file"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = ""; // allow picking the same file again after an error
            if (file) start(file);
          }}
        />
      </div>

      {error && !busy && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
