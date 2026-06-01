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
          900: "#000000",
          800: "#111111",
          700: "#222222",
        },
        bullish: "#00ff00",
        bearish: "#ff0000",
        gold: "#ffaa00",
        charcoal: {
          900: "#000000",
          800: "#0a0a0a",
          700: "#1a1a1a",
        }
      },
      fontFamily: {
        outfit: ["Outfit", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        marquee: 'marquee 25s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(-100%)' },
        }
      }
    },
  },
  plugins: [
    require("flowbite/plugin"),
    require("preline/plugin"),
  ],
};
