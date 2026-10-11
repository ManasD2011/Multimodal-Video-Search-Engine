import { useCallback, useEffect, useState } from "react";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "vs-theme";
const themeColors = { light: "#F3EFE6", dark: "#14110F" } as const;

function readPreference(): ThemePreference {
  try {
    const preference = localStorage.getItem(STORAGE_KEY);
    if (
      preference === "light" ||
      preference === "dark" ||
      preference === "system"
    ) {
      return preference;
    }
  } catch {
    return "system";
  }
  return "system";
}

function applyTheme(preference: ThemePreference, animate: boolean): void {
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const resolved = preference === "system"
    ? (systemDark ? "dark" : "light")
    : preference;
  const root = document.documentElement;
  if (animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    root.classList.add("theme-transition");
    window.setTimeout(() => root.classList.remove("theme-transition"), 200);
  }
  root.dataset.theme = resolved;
  root.dataset.themePref = preference;
  root.style.colorScheme = resolved;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", themeColors[resolved]);
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(readPreference);

  useEffect(() => {
    const alreadyApplied =
      document.documentElement.dataset.themePref === preference;
    applyTheme(preference, !alreadyApplied);
    try {
      localStorage.setItem(STORAGE_KEY, preference);
    } catch {
      // Theme selection remains usable when browser storage is blocked.
    }
    if (preference !== "system") return;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const updateSystemTheme = () => applyTheme("system", true);
    media.addEventListener("change", updateSystemTheme);
    return () => media.removeEventListener("change", updateSystemTheme);
  }, [preference]);

  const cycle = useCallback(() => {
    setPreference((current) =>
      current === "system" ? "light" : current === "light" ? "dark" : "system",
    );
  }, []);

  return { preference, setPreference, cycle };
}
