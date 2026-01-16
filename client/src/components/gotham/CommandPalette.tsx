import React, { useState, useEffect } from 'react';
import { Command } from 'cmdk';
import { Search } from 'lucide-react';
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
            className="fixed inset-0 bg-black/50 backdrop-blur-[2px] z-50"
            onClick={onClose}
          />

          {/* Command Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 flex items-center justify-center p-4 z-50"
          >
            <Command
              className="gotham-panel overflow-hidden shadow-gotham w-full max-w-2xl max-h-[90vh]"
              label="Command Menu"
            >
              {/* Search Input */}
              <div className="flex items-center gap-2.5 px-3 py-2.5 border-b border-gotham-gray-800/50">
                <Search className="w-4 h-4 text-gotham-blueprint-400/80" />
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder={placeholder}
                  autoFocus
                  className="flex-1 bg-transparent outline-none text-gotham-gray-100 placeholder:text-gotham-gray-500 text-sm"
                />
                <kbd className="px-1.5 py-0.5 text-xs font-mono bg-gotham-dark-300/50 text-gotham-gray-500 border border-gotham-gray-800/50 rounded">
                  ESC
                </kbd>
              </div>

              {/* Command List */}
              <Command.List className="max-h-[calc(90vh-5rem)] overflow-auto gotham-scrollbar p-1.5">
                <Command.Empty className="py-8 text-center text-sm text-gotham-gray-600">
                  No results found.
                </Command.Empty>

                {Object.entries(groupedCommands).map(([category, items]) => (
                  <Command.Group
                    key={category}
                    heading={category}
                    className="[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-gotham-gray-600 [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide"
                  >
                    {items.map((command) => (
                      <Command.Item
                        key={command.id}
                        value={`${command.label} ${command.description || ''}`}
                        onSelect={() => handleSelect(command)}
                        className={cn(
                          'flex items-center justify-between gap-2.5 px-2.5 py-2 mb-0.5 rounded cursor-pointer',
                          'text-sm text-gotham-gray-100',
                          'data-[selected=true]:bg-gotham-blueprint-400/15 data-[selected=true]:text-gotham-blueprint-400',
                          'hover:bg-gotham-dark-300/50 transition-colors'
                        )}
                      >
                        <div className="flex items-center gap-2.5 flex-1 min-w-0">
                          {command.icon && (
                            <span className="flex-shrink-0 text-gotham-gray-500 w-4 h-4">
                              {command.icon}
                            </span>
                          )}
                          <div className="flex flex-col flex-1 min-w-0">
                            <span className="font-medium truncate">{command.label}</span>
                            {command.description && (
                              <span className="text-xs text-gotham-gray-600 truncate mt-0.5">
                                {command.description}
                              </span>
                            )}
                          </div>
                        </div>
                        {command.shortcut && (
                          <kbd className="px-1.5 py-0.5 text-xs font-mono bg-gotham-dark-300/50 text-gotham-gray-500 border border-gotham-gray-800/50 rounded flex-shrink-0">
                            {command.shortcut}
                          </kbd>
                        )}
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
