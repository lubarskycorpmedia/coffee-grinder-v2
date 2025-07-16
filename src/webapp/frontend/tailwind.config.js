/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coffee: {
          black: '#1A0E0A',      // Глубокий чёрный кофе (фон)
          dark: '#2F1B14',       // Тёмный кофе (панели)
          medium: '#5D4037',     // Кофе с молоком (границы)
          light: '#8D6E63',      // Светлый кофе (текст)
          cream: '#BCAAA4',      // Молоко/сливки (активные элементы)
          foam: '#F5F5DC',       // Белая пенка (акценты)
          espresso: '#3E2723',   // Эспрессо (карточки)
          mocha: '#4E342E',      // Мокко (кнопки)
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      }
    },
  },
  plugins: [],
} 