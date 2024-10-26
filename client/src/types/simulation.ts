// client/src/types/simulation.ts
export type ParticleType = 'creature' | 'plant';

export type Diet = 'herbivore' | 'carnivore' | 'omnivore';

export type ReproductionStyle = 'self_replicating' | 'two_parents';

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
  diet: Diet;
  reproductionStyle: ReproductionStyle;
  packMentality: number;
  highEnergyHungerTime: number;
  meetingCount: Record<string, number>;
  groupId?: string;
  isChild: boolean;
  timeInGroup: number;
}

export interface ParticleRules {
  reproductionRate: number;
  energyConsumption: number;
  maxSpeed: number;
  visionRange: number;
  socialDistance: number;
  particleType: ParticleType;
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

export interface ParticleGroup {
  id: string;
  memberIds: Set<string>;
  speciesId: string;
  parentIds?: Set<string>;
  childId?: string;
}

export interface Species {
  id: string;
  name: string;
  color: string;
  baseRules: ParticleRules;
  population: number;
  diet: Diet;
  reproductionStyle: ReproductionStyle;
}

export interface SimulationState {
  particles: Map<string, Particle>;
  species: Map<string, Species>;
  groups: Map<string, ParticleGroup>;
  worldWidth: number;
  worldHeight: number;
  tickCount: number;
}

export interface RenderOptions {
  showGrid: boolean;
  showVision: boolean;
  showEnergy: boolean;
  showGroups: boolean;
  showDiet: boolean;
  particleScale: number;
  gridSize: number;
}