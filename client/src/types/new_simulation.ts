// client/src/types/new_simulation.ts
export type EntityType = 'creature' | 'plant' | 'obstacle';

export type Trait = 'herbivore' | 'carnivore' | 'omnivore' | 'self_replicating' | 'two_parents';

export interface Position {
  x: number;
  y: number;
}

export interface Velocity {
  x: number;
  y: number;
}

export interface Entity {
  id: string;
  position: Position;
  velocity: Velocity;
  health: number;
  energy: number;
  size: number;
  speciesId: string;
  packId?: string;
  color: string;
  visionRange: number;
  isChild: boolean;
  type: EntityType;
}

export interface Pack {
  id: string;
  memberIds: Set<string>;
}

export interface Species {
  id: string;
  name: string;
  color: string;
  traits: Set<Trait>;
  population: number;
  type: EntityType;
}

export interface SimulationState {
  entities: Map<string, Entity>;
  species: Map<string, Species>;
  packs: Map<string, Pack>;
  worldWidth: number;
  worldHeight: number;
  tickRate: number;
}

export interface RenderOptions {
  showGrid: boolean;
  showVision: boolean;
  showHealth: boolean;
  showEnergy: boolean;
  showPacks: boolean;
  entityScale: number;
  gridSize: number;
}

// Camera types
export interface CameraTransform {
  zoom: number;
  panX: number;
  panY: number;
}

// Statistics types
export interface SpeciesStats {
  averageEnergy: number;
  averageHealth: number;
  population: number;
  childCount: number;
  packCount: number;
}

// WebSocket message types (Phase 3: Delta encoding + MessagePack)
export interface DeltaMessage {
  type: 'delta';
  frame: number;
  tick: number;
  deltaTime: number;
  state: string;
  entities: {
    added: Record<string, any>;
    modified: Record<string, any>;
    removed: string[];
  };
  packs: {
    added: Record<string, any>;
    modified: Record<string, any>;
    removed: string[];
  };
  species: Record<string, any>;
}

export interface FullStateMessage {
  type: 'full';
  state: any;
  frame: number;
  tick: number;
}

