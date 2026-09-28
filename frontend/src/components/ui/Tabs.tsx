import React from "react";
import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  icon?: React.ComponentType<{ className?: string }>;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div
      className={cn(
        "flex space-x-1 border-b border-white/[0.08] overflow-x-auto pb-px",
        className
      )}
      role="tablist"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            data-testid={`tab-${tab.id}`}
            className={cn(
              "group inline-flex items-center space-x-2 border-b-2 py-3 px-4 text-xs font-semibold whitespace-nowrap transition-all duration-180 focus:outline-none",
              isActive
                ? "border-[#FF7A18] text-[#FF9A3D]"
                : "border-transparent text-[#A7AFBD] hover:border-white/20 hover:text-[#F5F7FA]"
            )}
          >
            {Icon && (
              <Icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  isActive
                    ? "text-[#FF7A18]"
                    : "text-[#6F7785] group-hover:text-[#A7AFBD]"
                )}
              />
            )}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={cn(
                  "ml-1.5 rounded-full px-2 py-0.5 text-[10px] font-mono",
                  isActive
                    ? "bg-[#FF7A18]/20 text-[#FF9A3D]"
                    : "bg-[#151B24] text-[#A7AFBD]"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
