import React from 'react';
import { cn } from '@/lib/utils';

export interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  className?: string;
}

export function MetricCard({
  label,
  value,
  subtitle,
  icon,
  trend,
  className,
}: MetricCardProps) {
  const getTrendColor = () => {
    if (!trend) return '';
    if (trend.direction === 'up') return 'text-gotham-success';
    if (trend.direction === 'down') return 'text-gotham-error';
    return 'text-gotham-gray-500';
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend.direction === 'up') return '▲';
    if (trend.direction === 'down') return '▼';
    return '●';
  };

  return (
    <div
      className={cn(
        'gotham-panel p-4 flex flex-col gap-2',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-gotham-gray-500 uppercase tracking-wider font-medium">
          {label}
        </span>
        {icon && (
          <span className="text-gotham-blueprint-400 opacity-60">
            {icon}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-mono font-semibold text-gotham-gray-100">
          {typeof value === 'number' ? value.toFixed(2) : value}
        </span>
        {trend && (
          <span className={cn('text-xs font-mono font-medium flex items-center gap-1', getTrendColor())}>
            <span>{getTrendIcon()}</span>
            <span>{Math.abs(trend.value).toFixed(1)}%</span>
          </span>
        )}
      </div>

      {subtitle && (
        <span className="text-xs text-gotham-gray-600 font-mono">
          {subtitle}
        </span>
      )}
    </div>
  );
}
