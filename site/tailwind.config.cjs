// Build-only configuration. Tailwind CLI 3.4.17.
module.exports = {
      content: [require('path').join(__dirname, 'index.html')],
      theme: {
        extend: {
          colors: {
            ink: {
              DEFAULT: '#0a0a0b',
              light: '#1c1c1f',
              muted: '#4a4a52'
            },
            paper: {
              DEFAULT: '#fcfcfc',
              alt: '#f2f3f5',
              dark: '#e4e6eb'
            },
            rise: {
              DEFAULT: '#005073',
              light: '#007A99',
              bg: '#e6f3f7'
            },
            status: {
              err: '#b91c1c',
              errBg: '#fef2f2',
              ok: '#15803d',
              okBg: '#f0fdf4'
            }
          },
          fontFamily: {
            sans: ['"IBM Plex Sans"', 'sans-serif'],
            serif: ['Fraunces', 'serif'],
            mono: ['"IBM Plex Mono"', 'monospace'],
          },
          animation: {
            'fade-in-up': 'fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
          },
          keyframes: {
            fadeInUp: {
              '0%': { opacity: '0', transform: 'translateY(16px)' },
              '100%': { opacity: '1', transform: 'translateY(0)' },
            }
          }
        }
      }
    };
