/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        // Gotham Blueprint Colors
        gotham: {
          blueprint: {
            50: '#E1F0F7',
            100: '#C4E1EF',
            200: '#8AC3DF',
            300: '#4FA5CF',
            400: '#2B95D6',
            500: '#215DB0',
            600: '#1F4B99',
            700: '#1A3A75',
            800: '#14294A',
            900: '#0E5A8A',
          },
          dark: {
            100: '#394B59',
            200: '#30404D',
            300: '#252A31',
            400: '#1C2127',
            500: '#0E1317',
          },
          gray: {
            100: '#F5F8FA',
            200: '#EBF1F5',
            300: '#D8E1E8',
            400: '#CED9E0',
            500: '#A7B6C2',
            600: '#8A9BA8',
            700: '#738694',
            800: '#5C7080',
            900: '#404854',
          },
          success: '#0F9960',
          warning: '#FFC940',
          error: '#DB3737',
        },
        // Legacy colors (keep for compatibility with old /sim route)
        gray: {
          900: '#121212',
          800: '#1e1e1e',
          700: '#2d2d2d',
          600: '#3d3d3d',
          500: '#4d4d4d',
          400: '#5d5d5d',
          300: '#6d6d6d',
          200: '#7d7d7d',
          100: '#8d8d8d',
        },
        blue: {
          900: '#1a365d',
          800: '#1e429f',
          700: '#1a4d8c',
          600: '#3182ce',
          500: '#4299e1',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', '"SF Mono"', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'gotham-sm': '0 0 4px rgba(43, 149, 214, 0.3)',
        'gotham': '0 0 8px rgba(43, 149, 214, 0.3)',
        'gotham-lg': '0 0 12px rgba(43, 149, 214, 0.3)',
        'gotham-inner': 'inset 0 0 4px rgba(43, 149, 214, 0.3)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    }
  },
  plugins: [require("tailwindcss-animate")],
}