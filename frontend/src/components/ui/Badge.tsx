import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "outline" | "primary" | "neutral";
}

export function Badge({ className, variant = "default", children, ...props }: BadgeProps) {
  const variants = {
    default: "bg-[#151B24] text-[#A7AFBD] border border-white/10",
    primary: "bg-[#FF7A18]/12 text-[#FF9A3D] border border-[#FF7A18]/30",
    success: "bg-[#28C76F]/10 text-[#28C76F] border border-[#28C76F]/25",
    warning: "bg-[#FFB020]/10 text-[#FFB020] border border-[#FFB020]/25",
    danger: "bg-[#FF4D4D]/10 text-[#FF4D4D] border border-[#FF4D4D]/25",
    outline: "border border-white/15 text-[#F5F7FA]",
    neutral: "bg-[#111722] text-[#A7AFBD] border border-white/10",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-mono font-medium tracking-wide transition-colors",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
