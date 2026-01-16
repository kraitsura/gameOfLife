import React from 'react';
import { cn } from '@/lib/utils';

export interface GothamButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export function GothamButton({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className,
  disabled,
  ...props
}: GothamButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium border transition-all duration-200 focus:outline-none';

  const variantStyles = {
    primary: 'bg-gotham-blueprint-400 hover:bg-gotham-blueprint-500 text-white border-gotham-blueprint-600 shadow-gotham-sm hover:shadow-gotham disabled:bg-gotham-gray-800 disabled:border-gotham-gray-800 disabled:text-gotham-gray-600 disabled:shadow-none',
    secondary: 'bg-gotham-dark-300 hover:bg-gotham-dark-200 text-gotham-gray-100 border-gotham-gray-800 disabled:bg-gotham-dark-400 disabled:text-gotham-gray-700',
    ghost: 'bg-transparent hover:bg-gotham-dark-300 text-gotham-gray-100 border-transparent hover:border-gotham-gray-800 disabled:text-gotham-gray-700 disabled:hover:bg-transparent',
    danger: 'bg-gotham-error hover:bg-red-600 text-white border-red-700 shadow-gotham-sm hover:shadow-gotham disabled:bg-gotham-gray-800 disabled:border-gotham-gray-800 disabled:text-gotham-gray-600',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      className={cn(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        disabled && 'cursor-not-allowed',
        className
      )}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
}
