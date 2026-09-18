/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canopy: {
          bg: '#F6F7F3',
          primary: '#17352B',
          green: '#237A68',
          teal: '#3D8B78',
          sage: '#E5EEE8',
          border: '#DCE4DF',
          muted: '#66756F',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Merriweather', 'serif'], // Used for the Hero heading
      }
    },
  },
  plugins: [],
}