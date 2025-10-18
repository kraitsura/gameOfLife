import React from 'react';
import { cn } from '@/lib/utils';

export interface GothamBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export function GothamBadge({ children, variant = 'default', className }: GothamBadgeProps) {
  const baseStyles = 'inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium border';

  const variantStyles = {
    default: 'bg-gotham-dark-300 text-gotham-gray-100 border-gotham-gray-800',
    success: 'bg-gotham-success/20 text-green-300 border-gotham-success',
    warning: 'bg-gotham-warning/20 text-yellow-300 border-gotham-warning',
    error: 'bg-gotham-error/20 text-red-300 border-gotham-error',
    info: 'bg-gotham-blueprint-400/20 text-blue-300 border-gotham-blueprint-400',
  };

  return (
    <span className={cn(baseStyles, variantStyles[variant], className)}>
      {children}
    </span>
  );
}
