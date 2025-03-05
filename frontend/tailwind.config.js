/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{html,js,svelte,ts}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)'],
        'sans-bold': ['var(--font-sans-bold)'],
        serif: ['var(--font-serif)'],
        display: ['var(--font-display)'],
      },
    },
  },
  plugins: [],
};