/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          900: "#0a0e17",
          850: "#0d1220",
          800: "#111827",
          750: "#161f30",
          700: "#1e293b",
          600: "#334155",
        },
        accent: { DEFAULT: "#38bdf8", 600: "#0ea5e9" },
        sev: {
          critical: "#f43f5e",
          high: "#fb923c",
          medium: "#facc15",
          low: "#38bdf8",
          info: "#64748b",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "ui-monospace", "monospace"],
      },
      keyframes: {
        "pulse-row": {
          "0%": { backgroundColor: "rgba(56,189,248,0.18)" },
          "100%": { backgroundColor: "transparent" },
        },
      },
      animation: { "pulse-row": "pulse-row 1.6s ease-out" },
    },
  },
  plugins: [],
};
