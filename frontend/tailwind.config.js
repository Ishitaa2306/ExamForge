/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ExamForge design token palette
        ivory:     '#F6F2EB',
        sand:      '#E9DFD1',
        terracotta:'#B8755D',
        sage:      '#788875',
        lavender:  '#A99AAF',
        olive:     '#A4A17C',
        charcoal:  '#302E2B',
        warmgray:  '#827B72',
        rose:      '#D6A69A',
        cream:     '#FCFAF6',
      },
      fontFamily: {
        sans:       ['Manrope', 'Plus Jakarta Sans', 'DM Sans', 'system-ui', 'sans-serif'],
        display:    ['"Instrument Serif"', '"Plus Jakarta Sans"', 'serif'],
        body:       ['Manrope', 'DM Sans', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        xs:   ['0.75rem',  { lineHeight: '1.5' }],
        sm:   ['0.875rem', { lineHeight: '1.6' }],
        base: ['1rem',     { lineHeight: '1.65' }],
        lg:   ['1.125rem', { lineHeight: '1.6' }],
        xl:   ['1.25rem',  { lineHeight: '1.5' }],
        '2xl':['1.5rem',   { lineHeight: '1.4' }],
        '3xl':['1.875rem', { lineHeight: '1.3' }],
        '4xl':['2.25rem',  { lineHeight: '1.2' }],
        '5xl':['3rem',     { lineHeight: '1.15' }],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.5rem',
      },
      boxShadow: {
        soft:    '0 2px 8px 0 rgba(48, 46, 43, 0.08)',
        card:    '0 4px 16px 0 rgba(48, 46, 43, 0.10)',
        raised:  '0 8px 32px 0 rgba(48, 46, 43, 0.12)',
      },
      transitionDuration: {
        DEFAULT: '200ms',
        fast:    '150ms',
        slow:    '400ms',
      },
      animation: {
        'fade-in':   'fadeIn 0.3s ease-in-out',
        'slide-up':  'slideUp 0.3s ease-out',
        'pulse-soft':'pulseSoft 2s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.6' },
        },
      },
      backgroundImage: {
        'ivory-gradient': 'linear-gradient(135deg, #F6F2EB 0%, #FCFAF6 100%)',
        'warm-gradient':  'linear-gradient(135deg, #E9DFD1 0%, #F6F2EB 100%)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
