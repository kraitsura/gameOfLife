import { useEffect, useCallback } from 'react';
import { useUIStore } from '../store/uiStore';

export function useCommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();

  const open = useCallback(() => {
    setCommandPaletteOpen(true);
  }, [setCommandPaletteOpen]);

  const close = useCallback(() => {
    setCommandPaletteOpen(false);
  }, [setCommandPaletteOpen]);

  const toggle = useCallback(() => {
    setCommandPaletteOpen(!commandPaletteOpen);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K to toggle command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggle();
      }

      // Escape to close
      if (e.key === 'Escape' && commandPaletteOpen) {
        e.preventDefault();
        close();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, toggle, close]);

  return {
    isOpen: commandPaletteOpen,
    open,
    close,
    toggle,
  };
}
