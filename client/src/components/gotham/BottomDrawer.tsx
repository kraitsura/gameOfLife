import React, { useState, useEffect, useRef } from 'react';
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
  const scrollRef = useRef<HTMLDivElement>(null);

  const activeTabContent = tabs.find((tab) => tab.id === activeTab);

  // Keyboard navigation: h/l (tabs) and j/k (scroll)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle if drawer is not collapsed and no input is focused
      if (isCollapsed || e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const currentIndex = tabs.findIndex((tab) => tab.id === activeTab);

      // Tab navigation: h (previous) and l (next)
      if (e.key === 'h' && currentIndex > 0) {
        e.preventDefault();
        setActiveTab(tabs[currentIndex - 1].id);
      } else if (e.key === 'l' && currentIndex < tabs.length - 1) {
        e.preventDefault();
        setActiveTab(tabs[currentIndex + 1].id);
      }
      // Scroll navigation: j (down) and k (up)
      else if (e.key === 'j' && scrollRef.current) {
        e.preventDefault();
        scrollRef.current.scrollBy({ top: 80, behavior: 'smooth' });
      } else if (e.key === 'k' && scrollRef.current) {
        e.preventDefault();
        scrollRef.current.scrollBy({ top: -80, behavior: 'smooth' });
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [activeTab, tabs, isCollapsed]);

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
      <div className="flex items-center justify-between border-b border-gotham-gray-900/50 bg-gotham-dark-400">
        <div className="flex items-center">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'relative px-6 py-2.5 text-sm font-medium transition-all duration-200 flex items-center gap-2.5 font-mono focus:outline-none',
                activeTab === tab.id
                  ? 'text-gotham-blueprint-400 bg-gotham-dark-300'
                  : 'text-gotham-gray-600 hover:text-gotham-gray-400 hover:bg-gotham-dark-300/50'
              )}
            >
              {/* Left accent line for active tab */}
              {activeTab === tab.id && (
                <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-gotham-blueprint-400" />
              )}
              {tab.icon && <span>{tab.icon}</span>}
              <span className="tracking-wide">{tab.label}</span>
              {tab.badge && (
                <span className="px-1.5 py-0.5 text-xs bg-gotham-blueprint-400/10 text-gotham-blueprint-400 font-mono border border-gotham-blueprint-400/30">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
          {!isCollapsed && (
            <div className="ml-6 flex flex-col gap-0.5 text-[11px] text-gotham-gray-700 font-mono tracking-wider">
              <div>
                <span className="text-gotham-gray-800">[</span>
                <span className="text-gotham-gray-600">h</span>
                <span className="text-gotham-gray-800">/</span>
                <span className="text-gotham-gray-600">l</span>
                <span className="text-gotham-gray-800">]</span>
              </div>
              <div>
                <span className="text-gotham-gray-800">[</span>
                <span className="text-gotham-gray-600">j</span>
                <span className="text-gotham-gray-800">/</span>
                <span className="text-gotham-gray-600">k</span>
                <span className="text-gotham-gray-800">]</span>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 px-4">
          {/* Cmd+K hint - always visible */}
          <div className="flex items-center gap-1.5 text-xs text-gotham-gray-500 font-mono mr-1">
            <kbd className="px-1.5 py-0.5 bg-gotham-dark-300/50 border border-gotham-gray-800/50 rounded text-gotham-gray-500">⌘K</kbd>
          </div>

          {!isCollapsed && (
            <>
              <button
                onClick={() => setPresetHeight('min')}
                className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300 focus:outline-none"
                title="Minimize height"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPresetHeight('max')}
                className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300 focus:outline-none"
                title="Maximize height"
              >
                <ChevronUp className="w-4 h-4" />
              </button>
            </>
          )}
          <button
            onClick={toggleCollapse}
            className="p-1.5 hover:bg-gotham-dark-200 rounded transition-colors text-gotham-gray-500 hover:text-gotham-gray-300 focus:outline-none"
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
          ref={(node) => {
            ref(node);
            scrollRef.current = node;
          }}
          className="h-full overflow-y-scroll gotham-scrollbar p-6"
          style={{ height: height - 49, scrollbarGutter: 'stable' }} // Subtract header height, prevent layout shift
        >
          {activeTabContent?.content}
        </div>
      )}
    </motion.div>
  );
}
