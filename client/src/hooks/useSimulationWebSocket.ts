import { useState, useEffect, useRef, useCallback } from 'react';
import { SimulationState, Trait } from '../types/new_simulation';

export interface UseSimulationWebSocketResult {
  state: SimulationState;
  isConnected: boolean;
  isPaused: boolean;
  togglePause: () => void;
  addSpecies: (name: string, color: string, traits: Trait[], initialCount: number) => void;
  sendMessage: (message: any) => void;
}

export function useSimulationWebSocket(websocketUrl: string): UseSimulationWebSocketResult {
  const [state, setState] = useState<SimulationState>({
    entities: new Map(),
    species: new Map(),
    packs: new Map(),
    worldWidth: 1600,
    worldHeight: 900,
    tickRate: 0,
  });

  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const isCleanupRef = useRef(false);

  useEffect(() => {
    // Reset cleanup flag for new connection
    isCleanupRef.current = false;

    wsRef.current = new WebSocket(websocketUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log('[WebSocket] Connected to simulation server');
    };

    wsRef.current.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Handle ping messages
      if (update.type === 'ping') {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'pong' }));
        }
        return;
      }

      setState((prevState) => {
        const newEntities = new Map();
        const newSpecies = new Map();
        const newPacks = new Map();

        // Update entities
        if (update.entities) {
          Object.entries(update.entities).forEach(([id, entity]: [string, any]) => {
            newEntities.set(id, {
              id: entity.id,
              speciesId: entity.speciesId,
              packId: entity.packId,
              type: entity.type,
              color: entity.color,
              size: entity.size,
              position: {
                x: entity.x,
                y: entity.y,
              },
              velocity: {
                x: entity.vx,
                y: entity.vy,
              },
              energy: entity.energy,
              health: entity.health,
              visionRange: entity.visionRange,
              isChild: entity.isChild,
            });
          });
        }

        // Update species
        if (update.species) {
          Object.entries(update.species).forEach(([id, species]: [string, any]) => {
            newSpecies.set(id, {
              id: species.id,
              name: species.name,
              color: species.color,
              type: species.type,
              population: species.population,
              traits: new Set(species.traits),  // Convert array to Set
            });
          });
        }

        // Update packs
        if (update.packs) {
          Object.entries(update.packs).forEach(([id, pack]: [string, any]) => {
            newPacks.set(id, {
              id: pack.id,
              memberIds: new Set(pack.memberIds),  // Convert array to Set
            });
          });
        }

        // Update pause state from server
        if (update.isRunning !== undefined) {
          setIsPaused(!update.isRunning);
        }

        return {
          ...prevState,
          entities: newEntities,
          species: newSpecies,
          packs: newPacks,
          tickRate: update.tickRate ?? prevState.tickRate,
          worldWidth: update.worldWidth ?? prevState.worldWidth,
          worldHeight: update.worldHeight ?? prevState.worldHeight,
        };
      });
    };

    wsRef.current.onclose = (event) => {
      setIsConnected(false);
      // Only log if not an intentional cleanup (e.g., React StrictMode unmount)
      if (!isCleanupRef.current) {
        console.log('[WebSocket] Disconnected from simulation server');
      }
    };

    wsRef.current.onerror = (error) => {
      // Only log errors if not during intentional cleanup
      if (!isCleanupRef.current) {
        console.error('[WebSocket] Error:', error);
      }
    };

    return () => {
      if (wsRef.current) {
        // Mark as intentional closure to prevent our custom error logging
        isCleanupRef.current = true;

        // Only close if connection is already established
        // Closing during CONNECTING state causes browser to log error
        if (wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.close();
        } else {
          // For CONNECTING/CLOSING/CLOSED states, just remove handlers
          // to prevent callbacks from firing and let it close naturally
          wsRef.current.onopen = null;
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.onmessage = null;
        }
      }
    };
  }, [websocketUrl]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message: WebSocket not connected');
    }
  }, []);

  const togglePause = useCallback(() => {
    sendMessage({
      type: isPaused ? 'start' : 'pause',
    });
    setIsPaused(!isPaused);
  }, [isPaused, sendMessage]);

  const addSpecies = useCallback(
    (name: string, color: string, traits: Trait[], initialCount: number) => {
      sendMessage({
        type: 'add_species',
        name,
        color,
        traits,
        initialCount,
      });
    },
    [sendMessage]
  );

  return {
    state,
    isConnected,
    isPaused,
    togglePause,
    addSpecies,
    sendMessage,
  };
}
