/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: '#111827',
        'surface-hover': '#1F2937',
        accent: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          glow: 'rgba(99, 102, 241, 0.25)',
        },
        stealth: {
          bg: 'rgba(15, 23, 42, 0.85)',
          border: 'rgba(255, 255, 255, 0.12)',
        }
      },
      backdropBlur: {
        stealth: '16px',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(99, 102, 241, 0.2)' },
          '100%': { boxShadow: '0 0 30px rgba(99, 102, 241, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
