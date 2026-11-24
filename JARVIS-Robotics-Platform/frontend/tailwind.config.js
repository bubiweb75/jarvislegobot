/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        jarvis: {
          dark: '#080d14',
          panel: '#0e1624',
          card: '#142033',
          border: '#1f3350',
          cyan: '#00e5ff',
          'cyan-dim': '#00838f',
          glow: '#00f0ff33',
          text: '#e2f1f8',
          muted: '#8ba2b5'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
