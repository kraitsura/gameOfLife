import React, { useState, useEffect } from 'react';
import { Command } from 'cmdk';
import { Search, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  shortcut?: string;
  category?: string;
  onSelect: () => void;
}

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
  placeholder?: string;
}

export function CommandPalette({
  isOpen,
  onClose,
  commands,
  placeholder = 'Type a command or search...',
}: CommandPaletteProps) {
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!isOpen) {
      setSearch('');
    }
  }, [isOpen]);

  // Group commands by category
  const groupedCommands = commands.reduce((acc, command) => {
    const category = command.category || 'General';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(command);
    return acc;
  }, {} as Record<string, CommandItem[]>);

  const handleSelect = (command: CommandItem) => {
    command.onSelect();
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Command Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-2xl z-50"
          >
            <Command
              className="gotham-panel overflow-hidden shadow-gotham-lg"
              label="Command Menu"
            >
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gotham-gray-800">
                <Search className="w-5 h-5 text-gotham-blueprint-400" />
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder={placeholder}
                  className="flex-1 bg-transparent outline-none text-gotham-gray-100 placeholder:text-gotham-gray-600 text-sm"
                />
                <kbd className="px-2 py-1 text-xs font-mono bg-gotham-dark-300 text-gotham-gray-500 border border-gotham-gray-800 rounded">
                  ESC
                </kbd>
              </div>

              {/* Command List */}
              <Command.List className="max-h-96 overflow-auto gotham-scrollbar p-2">
                <Command.Empty className="py-6 text-center text-sm text-gotham-gray-600">
                  No results found.
                </Command.Empty>

                {Object.entries(groupedCommands).map(([category, items]) => (
                  <Command.Group
                    key={category}
                    heading={category}
                    className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-gotham-gray-500 [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                  >
                    {items.map((command) => (
                      <Command.Item
                        key={command.id}
                        value={`${command.label} ${command.description || ''}`}
                        onSelect={() => handleSelect(command)}
                        className={cn(
                          'flex items-center justify-between gap-3 px-3 py-2.5 mb-1 rounded cursor-pointer',
                          'text-sm text-gotham-gray-100',
                          'data-[selected=true]:bg-gotham-blueprint-400/20 data-[selected=true]:text-gotham-blueprint-400',
                          'hover:bg-gotham-dark-300 transition-colors'
                        )}
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          {command.icon && (
                            <span className="flex-shrink-0 text-gotham-gray-500 data-[selected=true]:text-gotham-blueprint-400">
                              {command.icon}
                            </span>
                          )}
                          <div className="flex flex-col flex-1 min-w-0">
                            <span className="font-medium truncate">{command.label}</span>
                            {command.description && (
                              <span className="text-xs text-gotham-gray-600 truncate">
                                {command.description}
                              </span>
                            )}
                          </div>
                        </div>
                        {command.shortcut && (
                          <kbd className="px-2 py-1 text-xs font-mono bg-gotham-dark-300 text-gotham-gray-500 border border-gotham-gray-800 rounded flex-shrink-0">
                            {command.shortcut}
                          </kbd>
                        )}
                        <ArrowRight className="w-4 h-4 text-gotham-gray-600 flex-shrink-0 opacity-0 data-[selected=true]:opacity-100" />
                      </Command.Item>
                    ))}
                  </Command.Group>
                ))}
              </Command.List>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
