import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // SkyGuide design tokens (mirrors projet_ml_ch/frontend/styles.css :root).
      colors: {
        ink: "#151a22",
        muted: "#697483",
        line: "rgba(21,26,34,.13)",
        panel: "rgba(255,255,255,.88)",
        navy: "#101722",
        red: "#df1f3d",
        blue: "#2677c9",
        green: "#1d9b75",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 22px 55px rgba(27,53,86,.14)",
      },
      keyframes: {
        cloudMove: {
          from: { transform: "translateX(-15vw)" },
          to: { transform: "translateX(120vw)" },
        },
      },
      animation: {
        cloud: "cloudMove 28s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
