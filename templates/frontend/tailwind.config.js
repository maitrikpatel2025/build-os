/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '{{PRIMARY_COLOR_IMPORT}}',
        secondary: '{{SECONDARY_COLOR_IMPORT}}',
        neutral: '{{NEUTRAL_COLOR_IMPORT}}',
      },
      fontFamily: {
        heading: ['{{HEADING_FONT}}', 'sans-serif'],
        body: ['{{BODY_FONT}}', 'sans-serif'],
        mono: ['{{MONO_FONT}}', 'monospace'],
      },
    },
  },
  plugins: [],
};
