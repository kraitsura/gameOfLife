# server/app/models/simulation.py
from typing import Dict, List, Optional
from pydantic import BaseModel

class Position(BaseModel):
    x: float
    y: float

class Velocity(BaseModel):
    x: float
    y: float

class ParticleAttributes(BaseModel):
    energy: float = 100.0
    hunger: float = 0.0
    size: float = 3.0
    age: int = 0
    lastReproduced: int = 0
    lastAte: int = 0

class ParticleRules(BaseModel):
    reproductionRate: float
    energyConsumption: float
    maxSpeed: float
    visionRange: float
    socialDistance: float

class Particle(BaseModel):
    id: str
    position: Position
    velocity: Velocity
    attributes: ParticleAttributes
    rules: ParticleRules
    speciesId: str
    color: str

class Species(BaseModel):
    id: str
    name: str
    color: str
    baseRules: ParticleRules
    population: int = 0

class SimulationState(BaseModel):
    particles: Dict[str, Particle]
    species: Dict[str, Species]
    worldWidth: int
    worldHeight: int
    tickCount: int = 0