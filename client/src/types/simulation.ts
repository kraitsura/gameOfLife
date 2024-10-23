// client/src/types/simulation.ts
export interface Position {
  x: number;
  y: number;
}

export interface Velocity {
  x: number;
  y: number;
}

export interface ParticleAttributes {
  energy: number;
  hunger: number;
  size: number;
  age: number;
  lastReproduced: number;
  lastAte: number;
}

export interface ParticleRules {
  reproductionRate: number;
  energyConsumption: number;
  maxSpeed: number;
  visionRange: number;
  socialDistance: number;
}

export interface Particle {
  id: string;
  position: Position;
  velocity: Velocity;
  attributes: ParticleAttributes;
  rules: ParticleRules;
  speciesId: string;
  color: string;
}

export interface Species {
  id: string;
  name: string;
  color: string;
  baseRules: ParticleRules;
  population: number;
}

export interface SimulationState {
  particles: Map<string, Particle>;
  species: Map<string, Species>;
  worldWidth: number;
  worldHeight: number;
  tickCount: number;
}

export interface RenderOptions {
  showGrid: boolean;
  showVision: boolean;
  showEnergy: boolean;
  particleScale: number;
  gridSize: number;
}

export type UpdateCallback = (state: SimulationState) => void;