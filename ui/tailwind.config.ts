import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07111b",
        panel: "#0d1827",
        panelSoft: "#122033",
        edge: "#20334a",
        accent: "#80e7ff",
        accentWarm: "#f6c88f",
        success: "#58d6a2",
        danger: "#f48c7f",
        muted: "#91a4b8",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "sans-serif"],
        display: ["'Space Grotesk'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 24px 60px rgba(2, 6, 16, 0.45)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(128, 231, 255, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(128, 231, 255, 0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
} satisfies Config;
