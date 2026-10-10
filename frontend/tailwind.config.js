/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        security: {
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          safe: '#10b981',
          low: '#06b6d4',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#ef4444'
        }
      }
    },
  },
  plugins: [],
}
