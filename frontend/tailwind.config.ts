import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Semantic tokens backed by CSS variables (space-separated RGB channels),
        // so Tailwind opacity modifiers (bg-cyan/10) keep working and the whole
        // palette re-themes for light/dark by swapping variables. See globals.css.
        base: "rgb(var(--c-base) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        "surface-2": "rgb(var(--c-surface-2) / <alpha-value>)",
        line: "rgb(var(--c-line) / <alpha-value>)",
        fg: "rgb(var(--c-fg) / <alpha-value>)",
        cyan: {
          DEFAULT: "rgb(var(--c-cyan) / <alpha-value>)",
          soft: "rgb(var(--c-cyan) / <alpha-value>)",
        },
        danger: "rgb(var(--c-danger) / <alpha-value>)",
        warning: "rgb(var(--c-warning) / <alpha-value>)",
        muted: "rgb(var(--c-muted) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        fluid: "clamp(2.5rem, 6vw, 5.5rem)",
        "fluid-sm": "clamp(1.5rem, 3vw, 2.5rem)",
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(34,233,211,0.45)",
        "glow-danger": "0 0 40px -8px rgba(255,77,94,0.45)",
        card: "0 8px 40px -12px rgba(0,0,0,0.6)",
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(circle at 50% 0%, rgba(34,233,211,0.08), transparent 60%)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 1.8s cubic-bezier(0.4,0,0.6,1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
