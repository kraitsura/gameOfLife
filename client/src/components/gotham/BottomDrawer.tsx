import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronUp, ChevronDown, Minimize2, Maximize2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import useMeasure from 'react-use-measure';

export interface DrawerTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  badge?: string | number;
}

export interface BottomDrawerProps {
  tabs: DrawerTab[];
  defaultTab?: string;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  onHeightChange?: (height: number) => void;
  className?: string;
}

export function BottomDrawer({
  tabs,
  defaultTab,
  defaultHeight = 300,
  minHeight = 200,
  maxHeight = window.innerHeight * 0.7,
  onHeightChange,
  className,
}: BottomDrawerProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [height, setHeight] = useState(defaultHeight);
  const [isDragging, setIsDragging] = useState(false);
  const [ref, bounds] = useMeasure();

  const activeTabContent = tabs.find((tab) => tab.id === activeTab);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);

    const startY = e.clientY;
    const startHeight = height;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const delta = startY - moveEvent.clientY;
      const newHeight = Math.min(Math.max(startHeight + delta, minHeight), maxHeight);
      setHeight(newHeight);
      onHeightChange?.(newHeight);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const setPresetHeight = (preset: 'min' | 'default' | 'max') => {
    const newHeight = preset === 'min' ? minHeight : preset === 'max' ? maxHeight : defaultHeight;
    setHeight(newHeight);
    onHeightChange?.(newHeight);
  };

  return (
    <motion.div
      className={cn(
        'fixed bottom-0 left-0 right-0 z-30 bg-gotham-dark-400 border-t border-gotham-gray-800',
        className
      )}
      style={{ height: isCollapsed ? 'auto' : height }}
      initial={{ y: '100%' }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', damping: 30, stiffness: 300 }}
    >
      {/* Resize Handle */}
      {!isCollapsed && (
        <div
          onMouseDown={handleMouseDown}
          className={cn(
            'h-1 bg-gotham-gray-800 cursor-ns-resize hover:bg-gotham-blueprint-400 transition-colors',
            isDragging && 'bg-gotham-blueprint-400'
          )}
        />
      )}

      {/* Header with Tabs */}
      <div className="flex items-center justify-between border-b border-gotham-gray-800 bg-gotham-dark-300">
        <div className="flex items-center">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-6 py-3 text-sm font-medium uppercase tracking-wider transition-all duration-200 border-b-2 flex items-center gap-2',
                activeTab === tab.id
                  ? 'text-gotham-blueprint-400 border-gotham-blueprint-400 bg-gotham-dark-400'
                  : 'text-gotham-gray-500 border-transparent hover:text-gotham-gray-300 hover:bg-gotham-dark-200'
              )}
            >
              {tab.icon && <span>{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-gotham-blueprint-400/20 text-gotham-blueprint-400 rounded font-mono">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 px-4">
          {!isCollapsed && (
            <>
              <button
                onClick={() => setPresetHeight('min')}
                className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300"
                title="Minimize height"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPresetHeight('max')}
                className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300"
                title="Maximize height"
              >
                <ChevronUp className="w-4 h-4" />
              </button>
            </>
          )}
          <button
            onClick={toggleCollapse}
            className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300"
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            {isCollapsed ? (
              <Maximize2 className="w-4 h-4" />
            ) : (
              <Minimize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div
          ref={ref}
          className="h-full overflow-auto gotham-scrollbar p-6"
          style={{ height: height - 49 }} // Subtract header height
        >
          {activeTabContent?.content}
        </div>
      )}
    </motion.div>
  );
}
