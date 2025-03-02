// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ['./src/**/*.{html,js,svelte,ts}'],
    theme: {
      extend: {
        fontFamily: {
          sans: ['var(--font-sans)'], // Utilise la variable CSS --font-sans
          'sans-bold': ['var(--font-sans-bold)'], // Utilise --font-sans-bold
          serif: ['var(--font-serif)'], // Utilise --font-serif
          display: ['var(--font-display)'], // Utilise --font-display
        },
      },
    },
    plugins: [],
  };