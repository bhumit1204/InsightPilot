import { BackendStatus } from "@/components/backend-status";

import { Logo } from "./logo";
import { ThemeToggle } from "./theme-toggle";

export function SiteHeader() {
  return (
    <header className="border-b border-rule bg-paper">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <div className="flex items-center gap-4">
          <div className="hidden sm:block">
            <BackendStatus />
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}