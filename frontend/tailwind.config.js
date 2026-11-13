/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          900: '#14532d',
        },
        slateDark: '#0b0f19',
        cardDark: 'rgba(17, 24, 39, 0.75)',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(56, 189, 248, 0.35)',
        'glow-purple': '0 0 20px rgba(168, 85, 247, 0.35)',
      }
    },
  },
  plugins: [],
}
