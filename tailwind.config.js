/** @type {import('tailwindcss').Config} */
module.exports = {

  content: ["./kite_copier/static/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],

  daisyui: {
    themes: ["bumblebee", "retro", "cyberpunk", "valentine", "cmyk", "winter", "nord"],
    base: true,
    styled: true,
    utils: true,
    prefix: "",
    logs: false,
    themeRoot: ":root",
  },
}

