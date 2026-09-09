/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      colors: {
        wine: {
          50: '#FDF8F5',
          100: '#FBF0EB',
          200: '#F5DCD0',
          300: '#EEB9A5',
          400: '#E17456',
          500: '#C73E28',
          600: '#A42A1D',
          700: '#7A1C15',
          800: '#6B1D2F', // Signature ilcolletinto burgundy wine tone!
          900: '#4A1220',
          950: '#2A0812',
        },
        gold: {
          400: '#A38558',
          500: '#8F7142', // Signature ilcolletinto gold/tan accent tone!
          600: '#755B32',
        },
        cream: '#FDFBF9' // Signature ilcolletinto warm cream background!
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Playfair Display', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
