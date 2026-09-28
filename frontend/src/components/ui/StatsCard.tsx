import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

export interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  badge?: {
    text: string;
    variant?: "default" | "success" | "warning" | "danger" | "primary" | "neutral";
  };
  testId?: string;
  className?: string;
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = "text-[#FF7A18]",
  badge,
  testId,
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-white/[0.08] bg-[#0D1117] p-5 shadow-sm transition-all duration-200 hover-lift-card hover:border-[#FF7A18]/30",
        className
      )}
      data-testid={testId}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-mono font-medium uppercase tracking-wider text-[#A7AFBD]">
            {title}
          </p>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-display font-bold tracking-tight text-[#F5F7FA]">
              {value}
            </span>
          </div>
          {subtitle && (
            <p className="text-xs text-[#6F7785] pt-0.5">
              {subtitle}
            </p>
          )}
        </div>
        <div className="rounded-xl bg-[#151B24] border border-white/10 p-2.5">
          <Icon className={cn("h-5 w-5", iconColor)} />
        </div>
      </div>
      {badge && (
        <div className="mt-3 border-t border-white/[0.06] pt-2.5">
          <span className="text-[11px] font-mono font-medium text-[#FF9A3D]">
            {badge.text}
          </span>
        </div>
      )}
    </div>
  );
}
