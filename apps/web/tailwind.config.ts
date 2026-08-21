import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        surface: "#111111",
        card: "#161616",
        primary: {
          DEFAULT: "#f59e0b",
          foreground: "#0a0a0a",
        },
        accent: {
          DEFAULT: "#f59e0b",
          foreground: "#0a0a0a",
        },
        foreground: "#fafafa",
        muted: {
          DEFAULT: "#161616",
          foreground: "#a1a1aa",
        },
        destructive: {
          DEFAULT: "#ef4444",
          foreground: "#ffffff",
        },
        gold: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
        },
        border: "rgba(255, 255, 255, 0.06)",
        input: "rgba(255, 255, 255, 0.08)",
        ring: "#f59e0b",
        // Twin card accent colors
        "twin-purple": "#a855f7",
        "twin-blue": "#3b82f6",
        "twin-green": "#22c55e",
        "twin-pink": "#ec4899",
        "twin-yellow": "#eab308",
        "twin-teal": "#14b8a6",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        "gold-sm": "0 0 10px rgba(245, 158, 11, 0.15)",
        "gold-md": "0 0 20px rgba(245, 158, 11, 0.2)",
        "gold-lg": "0 0 30px rgba(245, 158, 11, 0.3)",
        "card": "0 1px 3px rgba(0, 0, 0, 0.3)",
      },
    },
  },
  plugins: [],
};
export default config;
