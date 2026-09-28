"use client";

import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react";

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const STORAGE_KEY = "campuspulse-theme";

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("system");
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("dark");
  const [mounted, setMounted] = useState(false);

  // Apply theme to document root
  const applyTheme = useCallback((resolved: ResolvedTheme) => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (resolved === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
      root.style.colorScheme = "dark";
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
      root.style.colorScheme = "light";
    }
  }, []);

  // Update theme and persist to localStorage
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
    } catch {
      // Ignore localStorage errors (e.g. incognito)
    }

    const resolved = newTheme === "system" ? getSystemTheme() : newTheme;
    setResolvedTheme(resolved);
    applyTheme(resolved);
  }, [applyTheme]);

  // Toggle between light, dark, and system (or simple light/dark flip)
  const toggleTheme = useCallback(() => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  }, [theme, setTheme]);

  // Initial load
  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem(STORAGE_KEY) as Theme | null;
      const initialTheme: Theme =
        savedTheme === "light" || savedTheme === "dark" || savedTheme === "system"
          ? savedTheme
          : "system";

      setThemeState(initialTheme);
      const resolved = initialTheme === "system" ? getSystemTheme() : initialTheme;
      setResolvedTheme(resolved);
      applyTheme(resolved);
    } catch {
      // Fallback
      const resolved = getSystemTheme();
      setResolvedTheme(resolved);
      applyTheme(resolved);
    }
    setMounted(true);
  }, [applyTheme]);

  // Listen to OS preference changes
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = () => {
      // Only react if current theme setting is "system"
      const currentSaved = (localStorage.getItem(STORAGE_KEY) as Theme | null) || "system";
      if (currentSaved === "system") {
        const newResolved = mediaQuery.matches ? "dark" : "light";
        setResolvedTheme(newResolved);
        applyTheme(newResolved);
      }
    };

    // Modern and fallback event listeners
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    } else {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [applyTheme]);

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme: mounted ? resolvedTheme : "dark",
      setTheme,
      toggleTheme,
    }),
    [theme, resolvedTheme, mounted, setTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
