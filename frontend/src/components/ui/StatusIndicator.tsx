import React from "react";
import { cn } from "@/lib/utils";

export interface StatusIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  status: "healthy" | "degraded" | "offline" | "loading";
  label?: string;
}

export function StatusIndicator({
  status,
  label,
  className,
  ...props
}: StatusIndicatorProps) {
  const statusConfig = {
    healthy: {
      color: "bg-[#28C76F]",
      ping: "bg-[#28C76F]",
      defaultLabel: "Systems Operational",
    },
    degraded: {
      color: "bg-[#FFB020]",
      ping: "bg-[#FFB020]",
      defaultLabel: "Degraded Performance",
    },
    offline: {
      color: "bg-[#FF4D4D]",
      ping: "bg-[#FF4D4D]",
      defaultLabel: "System Offline",
    },
    loading: {
      color: "bg-[#FF7A18]",
      ping: "bg-[#FF9A3D]",
      defaultLabel: "Connecting...",
    },
  };

  const current = statusConfig[status];

  return (
    <div className={cn("inline-flex items-center space-x-2 text-xs font-mono font-medium", className)} {...props}>
      <span className="relative flex h-2 w-2">
        {status === "healthy" && (
          <span
            className={cn(
              "animate-ping absolute inline-flex h-full w-full rounded-full opacity-60",
              current.ping
            )}
          />
        )}
        <span className={cn("relative inline-flex rounded-full h-2 w-2", current.color)} />
      </span>
      <span className="text-[#A7AFBD]">{label || current.defaultLabel}</span>
    </div>
  );
}
