export type Theme = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "insightpilot-theme";

/**
 * Runs in <head> before the first paint, so a saved theme never flashes the wrong colours.
 * "system" means no data-theme attribute: the CSS then follows prefers-color-scheme.
 */
export const themeScript = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;

export function readTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    return saved === "light" || saved === "dark" ? saved : "system";
  } catch {
    return "system";
  }
}

export function applyTheme(theme: Theme) {
  try {
    if (theme === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private windows can block storage; the theme still applies for this visit.
  }
  if (theme === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", theme);
  window.dispatchEvent(new Event("insightpilot-theme-change"));
}