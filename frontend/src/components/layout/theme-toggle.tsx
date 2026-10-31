"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useSyncExternalStore } from "react";

import { cn } from "@/lib/cn";
import { applyTheme, readTheme, type Theme } from "@/lib/theme";

const OPTIONS: { value: Theme; label: string; Icon: typeof Sun }[] = [
  { value: "system", label: "Match system", Icon: Monitor },
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
];

function subscribe(onChange: () => void) {
  window.addEventListener("insightpilot-theme-change", onChange);
  window.addEventListener("storage", onChange); // another tab changed it
  return () => {
    window.removeEventListener("insightpilot-theme-change", onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function ThemeToggle() {
  // The server cannot know the saved theme, so it renders "system" and React updates after load.
  const theme = useSyncExternalStore(subscribe, readTheme, () => "system" as Theme);

  return (
    <fieldset className="flex rounded-md border border-rule bg-surface p-0.5">
      <legend className="sr-only">Colour theme</legend>
      {OPTIONS.map(({ value, label, Icon }) => (
        <label
          key={value}
          title={label}
          className={cn(
            "flex size-8 cursor-pointer items-center justify-center rounded text-ink-muted transition-colors",
            "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-1 has-[:focus-visible]:outline-chart-blue",
            theme === value ? "bg-terrain text-ink" : "hover:text-ink",
          )}
        >
          <input
            type="radio"
            name="theme"
            value={value}
            checked={theme === value}
            onChange={() => applyTheme(value)}
            className="sr-only"
          />
          <Icon aria-hidden className="size-4" />
          <span className="sr-only">{label}</span>
        </label>
      ))}
    </fieldset>
  );
}