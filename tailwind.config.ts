import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#1A2E4A",
          dark: "#132238",
          light: "#243d61",
        },
        gold: {
          DEFAULT: "#C9922A",
          dark: "#B07D1E",
          light: "#DBA84E",
        },
        surface: "#FFFFFF",
        background: "#F7F6F3",
        border: "#E5E7EB",
        "text-primary": "#2B2B2B",
        "text-secondary": "#6B7280",
      },
      fontFamily: {
        serif: ["var(--font-playfair)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      fontSize: {
        "h1-desktop": ["3.5rem", { lineHeight: "1.15", fontWeight: "700" }],
        "h2-desktop": ["2.5rem", { lineHeight: "1.2", fontWeight: "700" }],
        "h3-desktop": ["1.75rem", { lineHeight: "1.3", fontWeight: "600" }],
        "h1-mobile": ["2.25rem", { lineHeight: "1.2", fontWeight: "700" }],
        "h2-mobile": ["1.75rem", { lineHeight: "1.25", fontWeight: "700" }],
        "body-lg": ["1.125rem", { lineHeight: "1.7" }],
        "body-md": ["1rem", { lineHeight: "1.6" }],
      },
      boxShadow: {
        card: "0 2px 12px rgba(0,0,0,0.08)",
        "card-hover": "0 8px 24px rgba(0,0,0,0.12)",
      },
      borderRadius: {
        card: "12px",
        btn: "6px",
        field: "8px",
      },
      maxWidth: {
        site: "1280px",
      },
    },
  },
  plugins: [],
};

export default config;
