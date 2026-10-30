import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center gap-4 px-4 py-24 sm:px-6">
      <h1 className="text-3xl font-bold tracking-tight">This page does not exist</h1>
      <p className="max-w-prose text-ink-muted">
        The link may be wrong, or the analysis it pointed to has been deleted.
      </p>
      <Link href="/" className={buttonVariants({ variant: "primary", className: "self-start" })}>
        Upload a new file
      </Link>
    </main>
  );
}