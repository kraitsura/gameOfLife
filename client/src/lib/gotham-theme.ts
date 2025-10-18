// Gotham Design System - Inspired by Palantir's Blueprint UI
// Technical, blueprint-style aesthetic for data-driven applications

export const gothamColors = {
  // Primary Blues (Blueprint signature colors)
  blueprint: {
    50: '#E1F0F7',
    100: '#C4E1EF',
    200: '#8AC3DF',
    300: '#4FA5CF',
    400: '#2B95D6', // Primary action color
    500: '#215DB0',
    600: '#1F4B99',
    700: '#1A3A75',
    800: '#14294A',
    900: '#0E5A8A',
  },

  // Dark Backgrounds (Primary UI surfaces)
  dark: {
    100: '#394B59', // Tertiary surface
    200: '#30404D', // Secondary hover
    300: '#252A31', // Secondary surface
    400: '#1C2127', // Primary background
    500: '#0E1317', // Deep background
  },

  // Grays (Borders, text, disabled states)
  gray: {
    100: '#F5F8FA',
    200: '#EBF1F5',
    300: '#D8E1E8',
    400: '#CED9E0',
    500: '#A7B6C2',
    600: '#8A9BA8',
    700: '#738694',
    800: '#5C7080', // Primary border
    900: '#404854',
  },

  // Semantic Colors
  success: '#0F9960',
  warning: '#FFC940',
  error: '#DB3737',
  info: '#2B95D6',

  // Special Effects
  glow: {
    blue: 'rgba(43, 149, 214, 0.3)',
    success: 'rgba(15, 153, 96, 0.3)',
    warning: 'rgba(255, 201, 64, 0.3)',
    error: 'rgba(219, 55, 55, 0.3)',
  },
} as const;

export const gothamTypography = {
  fonts: {
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    mono: '"JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace',
  },
  sizes: {
    xs: '0.6875rem', // 11px
    sm: '0.75rem',   // 12px
    base: '0.875rem', // 14px
    lg: '1rem',      // 16px
    xl: '1.125rem',  // 18px
    '2xl': '1.25rem', // 20px
    '3xl': '1.5rem',  // 24px
  },
  weights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeights: {
    tight: '1.2',
    normal: '1.5',
    relaxed: '1.75',
  },
} as const;

export const gothamSpacing = {
  // 4px grid system
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
} as const;

export const gothamBorders = {
  width: {
    thin: '1px',
    medium: '2px',
    thick: '3px',
  },
  radius: {
    none: '0',
    sm: '2px',
    base: '3px',
    md: '4px',
    lg: '6px',
  },
  style: {
    solid: 'solid',
    dashed: 'dashed',
  },
} as const;

export const gothamShadows = {
  sm: `0 0 4px ${gothamColors.glow.blue}`,
  base: `0 0 8px ${gothamColors.glow.blue}`,
  lg: `0 0 12px ${gothamColors.glow.blue}`,
  inner: `inset 0 0 4px ${gothamColors.glow.blue}`,
  none: 'none',
} as const;

export const gothamAnimations = {
  duration: {
    fast: '100ms',
    normal: '200ms',
    slow: '300ms',
  },
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  },
} as const;

export const gothamZIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  overlay: 1030,
  modal: 1040,
  popover: 1050,
  tooltip: 1060,
} as const;

// Utility function for creating glow effects
export function createGlow(color: string, intensity: number = 0.3): string {
  return `0 0 8px rgba(${color}, ${intensity})`;
}

// Utility function for blueprint-style borders
export function blueprintBorder(color: string = gothamColors.gray[800]): string {
  return `${gothamBorders.width.thin} ${gothamBorders.style.solid} ${color}`;
}

// Utility function for monospace number formatting
export function formatMonospace(value: number, decimals: number = 2): string {
  return value.toFixed(decimals);
}
