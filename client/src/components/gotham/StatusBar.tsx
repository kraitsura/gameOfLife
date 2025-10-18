import React from 'react';
import { cn } from '@/lib/utils';

export interface StatusItem {
  key: string;
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
}

export interface StatusBarProps {
  items: StatusItem[];
  className?: string;
}

export function StatusBar({ items, className }: StatusBarProps) {
  return (
    <div
      className={cn(
        'h-8 bg-gotham-dark-400 border-t border-gotham-gray-800 flex items-center px-4 gap-6',
        className
      )}
    >
      {items.map((item) => (
        <div
          key={item.key}
          className="flex items-center gap-2 text-xs"
        >
          {item.icon && (
            <span className="text-gotham-blueprint-400">{item.icon}</span>
          )}
          <span className="text-gotham-gray-500 font-medium">{item.label}:</span>
          <span
            className={cn(
              'font-mono font-semibold',
              item.color || 'text-gotham-gray-100'
            )}
          >
            {typeof item.value === 'number' ? item.value.toFixed(2) : item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
