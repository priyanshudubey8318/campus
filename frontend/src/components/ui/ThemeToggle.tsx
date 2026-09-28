"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sun, Moon, Laptop, Check } from "lucide-react";
import { useTheme, Theme } from "@/lib/theme/theme-context";

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className = "", showLabel = false }: ThemeToggleProps) {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click or escape key
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const options: { value: Theme; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "system", label: "System", icon: Laptop },
  ];

  const currentIcon =
    theme === "system"
      ? Laptop
      : resolvedTheme === "dark"
      ? Moon
      : Sun;

  const CurrentIconComponent = currentIcon;

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        data-testid="theme-toggle"
        aria-label={`Current theme: ${theme}. Click to change theme`}
        aria-expanded={isOpen}
        className="flex items-center space-x-2 p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-[#A7AFBD] dark:hover:text-[#F5F7FA] dark:hover:bg-white/[0.08] transition-colors border border-transparent hover:border-slate-200 dark:hover:border-white/10"
      >
        <CurrentIconComponent className="h-4 w-4 text-[#FF7A18] transition-transform duration-200" />
        {showLabel && (
          <span className="text-xs font-medium capitalize">
            {theme === "system" ? `System (${resolvedTheme})` : theme}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          data-testid="theme-dropdown"
          className="absolute right-0 mt-2 w-44 rounded-xl border border-slate-200 bg-white shadow-xl dark:border-white/10 dark:bg-[#151B24] p-1.5 z-50 animate-in fade-in zoom-in-95"
        >
          <div className="px-2 py-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400 dark:text-[#6F7785]">
            Theme Mode
          </div>
          {options.map((opt) => {
            const Icon = opt.icon;
            const isSelected = theme === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                data-testid={`theme-option-${opt.value}`}
                onClick={() => {
                  setTheme(opt.value);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isSelected
                    ? "bg-[#FF7A18]/15 text-[#FF9A3D] font-semibold"
                    : "text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-[#A7AFBD] dark:hover:bg-white/[0.06] dark:hover:text-[#F5F7FA]"
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`h-4 w-4 ${isSelected ? "text-[#FF7A18]" : "text-slate-400 dark:text-[#6F7785]"}`} />
                  <span>{opt.label}</span>
                  {opt.value === "system" && (
                    <span className="text-[10px] opacity-70">
                      ({resolvedTheme})
                    </span>
                  )}
                </div>
                {isSelected && <Check className="h-3.5 w-3.5 text-[#FF7A18]" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
