/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        cinema: {
          bg: "#0d0d0d",
          card: "#1a1a2e",
          accent: "#e94560",
          gold: "#f5c518",
          blue: "#16213e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
