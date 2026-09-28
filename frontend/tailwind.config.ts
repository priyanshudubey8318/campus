import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-space-grotesk)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        dark: {
          DEFAULT: "#07090D",
          bg: "#07090D",
          surface: "#0D1117",
          secondary: "#111722",
          elevated: "#151B24",
        },
        brand: {
          50: "rgba(255, 122, 24, 0.06)",
          100: "rgba(255, 122, 24, 0.12)",
          200: "rgba(255, 122, 24, 0.20)",
          500: "#FF7A18",
          600: "#FF7A18",
          700: "#E66507",
          800: "#BF5000",
          900: "#993B00",
          DEFAULT: "#FF7A18",
        },
        accent: {
          DEFAULT: "#FF7A18",
          secondary: "#FF9A3D",
          soft: "rgba(255, 122, 24, 0.12)",
        },
        surface: {
          50: "#151B24",
          100: "#111722",
          200: "#0D1117",
          DEFAULT: "#0D1117",
        },
        navy: {
          800: "#151B24",
          900: "#0D1117",
          950: "#07090D",
        },
        status: {
          warning: "#FFB020",
          error: "#FF4D4D",
          success: "#28C76F",
        },
      },
      borderColor: {
        subtle: "rgba(255, 255, 255, 0.08)",
        hover: "rgba(255, 122, 24, 0.35)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
