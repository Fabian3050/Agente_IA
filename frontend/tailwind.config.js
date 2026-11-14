/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        teal: {
          500: '#00aea7',
          600: '#009690',
          700: '#007a75',
        },
        navy: {
          800: '#1a2332',
          900: '#0f172a',
        }
      }
    },
  },
  plugins: [],
}

