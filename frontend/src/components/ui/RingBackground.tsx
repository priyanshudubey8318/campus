import React from "react";

interface RingBackgroundProps {
  className?: string;
  variant?: "hero" | "subtle" | "card" | "dense";
  glowPosition?: "center" | "top" | "right";
}

export function RingBackground({
  className = "",
  variant = "hero",
  glowPosition = "top",
}: RingBackgroundProps) {
  // Glow gradient origin based on position
  const glowOrigin =
    glowPosition === "top"
      ? "50% 15%"
      : glowPosition === "right"
      ? "85% 20%"
      : "50% 45%";

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden select-none z-0 ${className}`}
    >
      {/* Warm Orange Atmosphere Glow */}
      <div
        className="absolute inset-0 transition-opacity duration-300"
        style={{
          background: `radial-gradient(ellipse 900px 600px at ${glowOrigin}, rgba(255, 122, 24, 0.12) 0%, rgba(255, 122, 24, 0.03) 45%, transparent 75%)`,
        }}
      />

      {/* Deep Graphite Vignette (Dark Mode) */}
      <div
        className="absolute inset-0 dark:block hidden"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, transparent 40%, rgba(7, 9, 13, 0.8) 100%)",
        }}
      />

      {/* Soft Crisp Vignette (Light Mode) */}
      <div
        className="absolute inset-0 dark:hidden block"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, transparent 40%, rgba(248, 250, 252, 0.8) 100%)",
        }}
      />

      {/* Concentric Precision Orbital Rings */}
      <svg
        className="absolute w-[200%] h-[200%] -left-[50%] -top-[30%] opacity-90 transition-opacity duration-700"
        viewBox="0 0 1600 1600"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient
            id="ringGrad1"
            cx="50%"
            cy="50%"
            r="50%"
            fx="50%"
            fy="50%"
          >
            <stop offset="0%" stopColor="#FF7A18" stopOpacity="0.25" />
            <stop offset="70%" stopColor="#808080" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#808080" stopOpacity="0.02" />
          </radialGradient>
          <linearGradient id="orbitFade" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FF7A18" stopOpacity="0.25" />
            <stop offset="50%" stopColor="#808080" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#808080" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Ring 1 - inner core */}
        <circle
          cx="800"
          cy="700"
          r="180"
          stroke="url(#orbitFade)"
          strokeWidth="1"
          strokeDasharray="4 6"
          className="opacity-50"
        />

        {/* Ring 2 */}
        <circle
          cx="800"
          cy="700"
          r="320"
          stroke="currentColor"
          strokeWidth="1"
          className="text-slate-400/20 dark:text-white/[0.05]"
        />

        {/* Ring 3 - signature accent ring */}
        <circle
          cx="800"
          cy="700"
          r="480"
          stroke="url(#orbitFade)"
          strokeWidth="1.2"
          className="opacity-75"
        />

        {/* Ring 4 - dashed guide */}
        <circle
          cx="800"
          cy="700"
          r="660"
          stroke="currentColor"
          strokeWidth="1"
          strokeDasharray="8 8"
          className="text-slate-400/20 dark:text-white/[0.04]"
        />

        {/* Ring 5 - wide orbital ring */}
        <circle
          cx="800"
          cy="700"
          r="860"
          stroke="rgba(255, 122, 24, 0.09)"
          strokeWidth="1.2"
        />

        {/* Ring 6 - outer atmosphere */}
        <circle
          cx="800"
          cy="700"
          r="1100"
          stroke="currentColor"
          strokeWidth="1"
          className="text-slate-400/15 dark:text-white/[0.03]"
        />

        {/* Ring 7 - distant outer horizon */}
        {variant !== "subtle" && (
          <circle
            cx="800"
            cy="700"
            r="1380"
            stroke="currentColor"
            strokeWidth="1"
            strokeDasharray="12 12"
            className="text-slate-400/10 dark:text-white/[0.02]"
          />
        )}

        {/* Editorial Accent Marks */}
        {variant === "hero" && (
          <>
            <line
              x1="800"
              y1="220"
              x2="800"
              y2="200"
              stroke="#FF7A18"
              strokeWidth="2"
              className="opacity-70"
            />
            <circle
              cx="800"
              cy="220"
              r="2.5"
              fill="#FF7A18"
              className="opacity-90"
            />
            <line
              x1="320"
              y1="700"
              x2="300"
              y2="700"
              stroke="currentColor"
              strokeWidth="1"
              className="text-slate-400/30 dark:text-white/20"
            />
            <line
              x1="1280"
              y1="700"
              x2="1300"
              y2="700"
              stroke="currentColor"
              strokeWidth="1"
              className="text-slate-400/30 dark:text-white/20"
            />
          </>
        )}
      </svg>
    </div>
  );
}
