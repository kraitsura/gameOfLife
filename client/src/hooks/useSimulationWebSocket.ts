import { useState, useEffect, useCallback } from 'react';
import { SimulationState, Trait } from '../types/new_simulation';
import { websocketManager } from '../lib/websocketManager';

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

  useEffect(() => {
    // Connect to WebSocket via singleton manager
    websocketManager.connect(websocketUrl);

    // Subscribe to WebSocket events
    const unsubscribe = websocketManager.subscribe(
      // onMessage (Phase 3: Support both full and delta updates)
      (update) => {
        setState((prevState) => {
          // Check message type - handle both full and delta updates
          if (update.type === 'delta') {
            // Delta update - apply incremental changes
            const newEntities = new Map(prevState.entities);
            const newPacks = new Map(prevState.packs);
            const newSpecies = new Map();

            // Apply entity changes
            if (update.entities) {
              // Add new entities
              if (update.entities.added) {
                Object.entries(update.entities.added).forEach(([id, entity]: [string, any]) => {
                  newEntities.set(id, {
                    id: entity.id,
                    speciesId: entity.speciesId,
                    packId: entity.packId,
                    type: entity.type,
                    color: entity.color,
                    size: entity.size,
                    position: { x: entity.x, y: entity.y },
                    velocity: { x: entity.vx, y: entity.vy },
                    energy: entity.energy,
                    health: entity.health,
                    visionRange: entity.visionRange,
                    isChild: entity.isChild,
                  });
                });
              }

              // Update modified entities
              if (update.entities.modified) {
                Object.entries(update.entities.modified).forEach(([id, entity]: [string, any]) => {
                  newEntities.set(id, {
                    id: entity.id,
                    speciesId: entity.speciesId,
                    packId: entity.packId,
                    type: entity.type,
                    color: entity.color,
                    size: entity.size,
                    position: { x: entity.x, y: entity.y },
                    velocity: { x: entity.vx, y: entity.vy },
                    energy: entity.energy,
                    health: entity.health,
                    visionRange: entity.visionRange,
                    isChild: entity.isChild,
                  });
                });
              }

              // Remove deleted entities
              if (update.entities.removed) {
                update.entities.removed.forEach((id: string) => {
                  newEntities.delete(id);
                });
              }
            }

            // Apply pack changes
            if (update.packs) {
              // Add new packs
              if (update.packs.added) {
                Object.entries(update.packs.added).forEach(([id, pack]: [string, any]) => {
                  newPacks.set(id, {
                    id: pack.id,
                    memberIds: new Set(pack.memberIds),
                  });
                });
              }

              // Update modified packs
              if (update.packs.modified) {
                Object.entries(update.packs.modified).forEach(([id, pack]: [string, any]) => {
                  newPacks.set(id, {
                    id: pack.id,
                    memberIds: new Set(pack.memberIds),
                  });
                });
              }

              // Remove deleted packs
              if (update.packs.removed) {
                update.packs.removed.forEach((id: string) => {
                  newPacks.delete(id);
                });
              }
            }

            // Update species (species data included in every delta)
            if (update.species) {
              Object.entries(update.species).forEach(([id, species]: [string, any]) => {
                newSpecies.set(id, {
                  id: species.id,
                  name: species.name,
                  color: species.color,
                  type: species.type,
                  population: species.population,
                  traits: new Set(species.traits),
                });
              });
            }

            // Update pause state from server
            if (update.state !== undefined) {
              setIsPaused(update.state !== 'running');
            }

            return {
              ...prevState,
              entities: newEntities,
              species: newSpecies,
              packs: newPacks,
              tickRate: update.tick ?? prevState.tickRate,
            };
          } else {
            // Full state update (type === 'full' or legacy format without type)
            const newEntities = new Map();
            const newSpecies = new Map();
            const newPacks = new Map();

            // Get state data (might be nested under 'state' key for full updates)
            const stateData = update.state || update;

            // Update entities
            if (stateData.entities) {
              Object.entries(stateData.entities).forEach(([id, entity]: [string, any]) => {
                newEntities.set(id, {
                  id: entity.id,
                  speciesId: entity.speciesId,
                  packId: entity.packId,
                  type: entity.type,
                  color: entity.color,
                  size: entity.size,
                  position: { x: entity.x, y: entity.y },
                  velocity: { x: entity.vx, y: entity.vy },
                  energy: entity.energy,
                  health: entity.health,
                  visionRange: entity.visionRange,
                  isChild: entity.isChild,
                });
              });
            }

            // Update species
            if (stateData.species) {
              Object.entries(stateData.species).forEach(([id, species]: [string, any]) => {
                newSpecies.set(id, {
                  id: species.id,
                  name: species.name,
                  color: species.color,
                  type: species.type,
                  population: species.population,
                  traits: new Set(species.traits),
                });
              });
            }

            // Update packs
            if (stateData.packs) {
              Object.entries(stateData.packs).forEach(([id, pack]: [string, any]) => {
                newPacks.set(id, {
                  id: pack.id,
                  memberIds: new Set(pack.memberIds),
                });
              });
            }

            // Update pause state from server
            if (stateData.isRunning !== undefined) {
              setIsPaused(!stateData.isRunning);
            } else if (stateData.state !== undefined) {
              setIsPaused(stateData.state !== 'running');
            }

            return {
              ...prevState,
              entities: newEntities,
              species: newSpecies,
              packs: newPacks,
              tickRate: update.tick ?? stateData.tickRate ?? prevState.tickRate,
              worldWidth: stateData.worldWidth ?? prevState.worldWidth,
              worldHeight: stateData.worldHeight ?? prevState.worldHeight,
            };
          }
        });
      },
      // onConnect
      () => {
        setIsConnected(true);
        console.log('[useSimulationWebSocket] Connected to simulation server');
      },
      // onDisconnect
      () => {
        setIsConnected(false);
        console.log('[useSimulationWebSocket] Disconnected from simulation server');
      },
      // onError
      (error) => {
        console.error('[useSimulationWebSocket] Error:', error);
      }
    );

    // Cleanup: Unsubscribe when component unmounts
    return unsubscribe;
  }, [websocketUrl]);

  const sendMessage = useCallback((message: any) => {
    websocketManager.send(message);
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
