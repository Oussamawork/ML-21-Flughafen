import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0b6e6e",
          dark: "#084f4f",
        },
      },
    },
  },
  plugins: [],
};

export default config;
