/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./node_modules/flowbite/**/*.js",
    "./node_modules/preline/dist/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          900: "#0f172a",
          800: "#1e293b",
        },
        bullish: "#22c55e",
        bearish: "#ef4444",
        gold: "#f59e0b",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [
    require("flowbite/plugin"),
    require("preline/plugin"),
  ],
};
