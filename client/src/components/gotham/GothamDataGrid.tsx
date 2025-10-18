import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface GothamDataGridProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
  selectedId?: string;
  getId?: (item: T) => string;
  className?: string;
  emptyMessage?: string;
}

export function GothamDataGrid<T>({
  data,
  columns,
  onRowClick,
  selectedId,
  getId,
  className,
  emptyMessage = 'No data available',
}: GothamDataGridProps<T>) {
  const [sortColumn, setSortColumn] = React.useState<string | null>(null);
  const [sortDirection, setSortDirection] = React.useState<'asc' | 'desc'>('asc');

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  return (
    <div className={cn('w-full overflow-auto gotham-scrollbar', className)}>
      <table className="w-full border-collapse">
        <thead className="bg-gotham-dark-300 sticky top-0 z-10">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  'px-4 py-3 text-xs font-semibold text-gotham-gray-400 uppercase tracking-wider border-b border-gotham-gray-800',
                  getAlignClass(column.align),
                  column.sortable && 'cursor-pointer select-none hover:bg-gotham-dark-200 transition-colors'
                )}
                style={{ width: column.width }}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center gap-2 justify-between">
                  <span>{column.header}</span>
                  {column.sortable && sortColumn === column.key && (
                    <span className="text-gotham-blueprint-400">
                      {sortDirection === 'asc' ? (
                        <ArrowUp className="w-3 h-3" />
                      ) : (
                        <ArrowDown className="w-3 h-3" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-sm text-gotham-gray-600"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item, index) => {
              const itemId = getId ? getId(item) : String(index);
              const isSelected = selectedId === itemId;

              return (
                <tr
                  key={itemId}
                  onClick={() => onRowClick?.(item)}
                  className={cn(
                    'gotham-data-row border-b border-gotham-gray-900',
                    onRowClick && 'cursor-pointer',
                    isSelected && 'bg-gotham-blueprint-900/30 border-gotham-blueprint-700'
                  )}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        'px-4 py-3 text-sm text-gotham-gray-100 font-mono',
                        getAlignClass(column.align)
                      )}
                    >
                      {column.render(item)}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
