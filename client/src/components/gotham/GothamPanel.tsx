import React from 'react';
import { motion } from 'framer-motion';
import { X, Minimize2, Maximize2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface GothamPanelProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  onClose?: () => void;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export function GothamPanel({
  title,
  children,
  className,
  onClose,
  collapsible = false,
  defaultCollapsed = false,
}: GothamPanelProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.15 }}
      className={cn('gotham-panel flex flex-col overflow-hidden', className)}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gotham-gray-800 bg-gotham-dark-300/50">
        <h3 className="text-sm font-semibold text-gotham-gray-100 uppercase tracking-wider">
          {title}
        </h3>
        <div className="flex items-center gap-2">
          {collapsible && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-gotham-dark-200 rounded transition-colors"
              title={isCollapsed ? 'Expand' : 'Collapse'}
            >
              {isCollapsed ? (
                <Maximize2 className="w-4 h-4 text-gotham-gray-500" />
              ) : (
                <Minimize2 className="w-4 h-4 text-gotham-gray-500" />
              )}
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-gotham-error/20 rounded transition-colors"
              title="Close"
            >
              <X className="w-4 h-4 text-gotham-gray-500 hover:text-gotham-error" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: 'auto' }}
          exit={{ height: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-auto gotham-scrollbar"
        >
          {children}
        </motion.div>
      )}
    </motion.div>
  );
}
