import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-180 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#07090D] disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]";

    const variants = {
      primary:
        "bg-[#FF7A18] text-[#07090D] font-semibold hover:bg-[#FF9A3D] focus:ring-[#FF7A18] shadow-[0_2px_14px_rgba(255,122,24,0.25)] hover:-translate-y-0.5",
      secondary:
        "bg-[#151B24] text-[#F5F7FA] border border-white/10 hover:border-[#FF7A18]/40 hover:bg-[#1C2430] focus:ring-[#FF7A18]/50 hover:-translate-y-0.5",
      outline:
        "border border-white/15 text-[#F5F7FA] hover:bg-white/[0.06] hover:border-[#FF7A18]/50 focus:ring-[#FF7A18] hover:-translate-y-0.5",
      ghost:
        "text-[#A7AFBD] hover:text-[#F5F7FA] hover:bg-white/[0.05] focus:ring-[#FF7A18]/40",
      danger:
        "bg-[#FF4D4D] text-white hover:bg-[#E63939] focus:ring-[#FF4D4D]/50 shadow-[0_2px_10px_rgba(255,77,77,0.25)] hover:-translate-y-0.5",
    };

    const sizes = {
      sm: "text-xs px-3 py-1.5",
      md: "text-sm px-4 py-2",
      lg: "text-base px-6 py-3 font-medium",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
