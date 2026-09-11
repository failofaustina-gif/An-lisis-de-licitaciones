import type { Config } from "tailwindcss";

// Paleta sobria orientada a research económico: fondo claro, pocos acentos de color.
// Se centraliza acá para no hardcodear colores sueltos en los componentes.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#111318",
          700: "#2b2f38",
          500: "#5b6270",
          300: "#9aa1ad",
          100: "#e6e8ec",
        },
        paper: "#fafaf8",
        accent: {
          DEFAULT: "#1f5f4f", // verde oscuro, único acento fuerte
          muted: "#4c7c6e",
        },
        warn: "#a15c00",
        danger: "#9c2b2b",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "IBM Plex Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
