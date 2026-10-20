/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { forest: { 50:'#eff8f1',100:'#d9efdf',500:'#347c50',600:'#246c49',700:'#1c5538',800:'#164b34',900:'#103b29' } }, fontFamily: { sans:['DM Sans','sans-serif'], display:['Manrope','sans-serif'] }, boxShadow: { soft:'0 12px 32px rgba(27,68,45,.08)' } } },
  plugins: [],
}
