"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Theme = "light" | "dark" | "system";
export type Depth = "quick" | "standard" | "deep";

export interface Preferences {
  theme: Theme;
  depth: Depth;
  /** Show a source preview when hovering a `[n]` citation. */
  citationPreview: boolean;
  sidebarOpen: boolean;
}

export const STORAGE_KEY = "ara.prefs.v1";

export const DEFAULT_PREFERENCES: Preferences = {
  theme: "system",
  depth: "standard",
  citationPreview: true,
  sidebarOpen: true,
};

export const DEPTH_OPTIONS: Record<
  Depth,
  { label: string; iterations: number; description: string }
> = {
  quick: {
    label: "Quick",
    iterations: 0,
    description: "One search pass. Fastest and cheapest.",
  },
  standard: {
    label: "Standard",
    iterations: 2,
    description: "Follows up on evidence gaps when needed.",
  },
  deep: {
    label: "Deep",
    iterations: 3,
    description: "Pushes harder on gaps. Slowest, most thorough.",
  },
};

/** Depth inferred from a run's stored iteration count. */
export function depthFromIterations(iterations: number | null): Depth | null {
  if (iterations === null || iterations === undefined) return null;
  if (iterations <= 0) return "quick";
  if (iterations <= 2) return "standard";
  return "deep";
}

interface PreferencesContextValue {
  preferences: Preferences;
  setPreference: <K extends keyof Preferences>(
    key: K,
    value: Preferences[K],
  ) => void;
  reset: () => void;
  /** The theme actually applied right now (system resolved to light/dark). */
  resolvedTheme: "light" | "dark";
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

function readStored(): Preferences {
  if (typeof window === "undefined") return DEFAULT_PREFERENCES;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    const parsed = JSON.parse(raw) as Partial<Preferences>;
    return { ...DEFAULT_PREFERENCES, ...parsed };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

function systemIsDark(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [systemDark, setSystemDark] = useState(false);

  // Hydrate from localStorage after mount so server and client markup match. The read is
  // deferred to a microtask so it does not trigger a synchronous cascading render.
  useEffect(() => {
    queueMicrotask(() => {
      setPreferences(readStored());
      setSystemDark(systemIsDark());
    });
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const resolvedTheme: "light" | "dark" =
    preferences.theme === "system"
      ? systemDark
        ? "dark"
        : "light"
      : preferences.theme;

  // Apply the theme to the document, and keep the scrollbar/color-scheme honest.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", resolvedTheme === "dark");
    root.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  const setPreference = useCallback(
    <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
      setPreferences((prev) => {
        const next = { ...prev, [key]: value };
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          // Storage can be unavailable (private mode); preferences still apply this session.
        }
        return next;
      });
    },
    [],
  );

  const reset = useCallback(() => {
    setPreferences(DEFAULT_PREFERENCES);
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo(
    () => ({ preferences, setPreference, reset, resolvedTheme }),
    [preferences, setPreference, reset, resolvedTheme],
  );

  return (
    <PreferencesContext.Provider value={value}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences(): PreferencesContextValue {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error("usePreferences must be used inside PreferencesProvider");
  }
  return context;
}
