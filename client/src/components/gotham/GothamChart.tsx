import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { gothamColors } from '@/lib/gotham-theme';

export interface GothamChartProps {
  data: any[];
  type?: 'line' | 'area' | 'bar';
  dataKeys: { key: string; name?: string; color?: string }[];
  xAxisKey: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  className?: string;
}

const GOTHAM_CHART_COLORS = [
  gothamColors.blueprint[400],
  gothamColors.success,
  gothamColors.warning,
  gothamColors.error,
  gothamColors.blueprint[600],
  gothamColors.blueprint[200],
];

export function GothamChart({
  data,
  type = 'line',
  dataKeys,
  xAxisKey,
  height = 300,
  showGrid = true,
  showLegend = true,
  className,
}: GothamChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="gotham-panel p-3 shadow-gotham">
        <p className="text-xs text-gotham-gray-500 font-medium mb-2 font-mono">
          {label}
        </p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-gotham-gray-400">{entry.name}:</span>
            </div>
            <span className="font-mono font-semibold text-gotham-gray-100">
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const chartProps = {
    data,
    margin: { top: 5, right: 10, left: 0, bottom: 5 },
  };

  const commonAxisProps = {
    stroke: gothamColors.gray[800],
    style: {
      fontSize: '11px',
      fill: gothamColors.gray[600],
      fontFamily: 'JetBrains Mono, monospace',
    },
  };

  const renderChart = () => {
    const ChartComponent = type === 'area' ? AreaChart : type === 'bar' ? BarChart : LineChart;

    return (
      <ResponsiveContainer width="100%" height={height} className={className}>
        <ChartComponent {...chartProps}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={gothamColors.gray[900]}
              opacity={0.5}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            {...commonAxisProps}
            tickLine={{ stroke: gothamColors.gray[800] }}
          />
          <YAxis
            {...commonAxisProps}
            tickLine={{ stroke: gothamColors.gray[800] }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              wrapperStyle={{
                fontSize: '11px',
                fontFamily: 'JetBrains Mono, monospace',
              }}
              iconType="circle"
            />
          )}
          {dataKeys.map((dataKey, index) => {
            const color = dataKey.color || GOTHAM_CHART_COLORS[index % GOTHAM_CHART_COLORS.length];
            const name = dataKey.name || dataKey.key;

            if (type === 'area') {
              return (
                <Area
                  key={dataKey.key}
                  type="monotone"
                  dataKey={dataKey.key}
                  name={name}
                  stroke={color}
                  fill={color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              );
            } else if (type === 'bar') {
              return (
                <Bar
                  key={dataKey.key}
                  dataKey={dataKey.key}
                  name={name}
                  fill={color}
                  opacity={0.8}
                />
              );
            } else {
              return (
                <Line
                  key={dataKey.key}
                  type="monotone"
                  dataKey={dataKey.key}
                  name={name}
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: color }}
                />
              );
            }
          })}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  return renderChart();
}
