/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'grid-dark': {
          950: '#0a0a0f',
          900: '#121218',
          850: '#161620',
          800: '#1a1a24',
          700: '#232330',
          600: '#2d2d3d',
          500: '#3d3d4d',
        },
        'electric-blue': {
          500: '#00d4ff',
          400: '#33ddff',
          300: '#66e6ff',
        },
        'safety-orange': {
          500: '#ff6b35',
          400: '#ff8555',
          300: '#ffa077',
        },
        'peak-red': {
          500: '#ff3366',
          400: '#ff5577',
          300: '#ff7799',
        },
        'success-green': {
          600: '#00cc6a',
          500: '#00ff88',
          400: '#33ffaa',
          300: '#66ffbb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-orange': '0 0 20px rgba(255, 107, 53, 0.3)',
        'inner-glow': 'inset 0 0 20px rgba(0, 212, 255, 0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 212, 255, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.8)' },
        },
      },
    },
  },
  plugins: [],
}
