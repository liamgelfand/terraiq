/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        forest: {
          50:  "#f0f7f1",
          100: "#d9eddb",
          200: "#b3dab8",
          300: "#7ec088",
          400: "#4da05c",
          500: "#2d8040",
          600: "#216630",
          700: "#1c5228",   // primary brand green
          800: "#183f20",
          900: "#14321a",
        },
        earth: {
          50:  "#fdf5ef",
          100: "#fae6d5",
          200: "#f4c9a8",
          300: "#eca573",
          400: "#e27b43",
          500: "#c85e27",
          600: "#a0491e",   // earthy brown
          700: "#7d3817",
          800: "#632d14",
          900: "#502512",
        },
        stone: {
          50:  "#fafaf9",
          100: "#f5f4f1",
          200: "#e8e6e1",
          300: "#d4d0c8",
          400: "#b0aa9d",
          500: "#8e8779",
          600: "#706960",
          700: "#5a5450",
          800: "#403d3a",
          900: "#292725",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
