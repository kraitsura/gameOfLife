# server/app/models/simulation.py
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from enum import Enum

class ParticleType(str, Enum):
    CREATURE = "creature"
    PLANT = "plant"

class Diet(str, Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"

class ReproductionStyle(str, Enum):
    SELF_REPLICATING = "self_replicating"
    TWO_PARENTS = "two_parents"

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
    diet: Diet
    reproductionStyle: ReproductionStyle
    packMentality: float = 0.5  # 0-1 scale
    highEnergyHungerTime: int = 0  # Tracks time with high energy/hunger
    meetingCount: Dict[str, int] = {}  # Tracks meetings with other particles
    groupId: Optional[str] = None  # ID of the group this particle belongs to
    isChild: bool = False
    timeInGroup: int = 0

class ParticleRules(BaseModel):
    reproductionRate: float
    energyConsumption: float
    maxSpeed: float
    visionRange: float
    socialDistance: float
    particleType: ParticleType = ParticleType.CREATURE

class Particle(BaseModel):
    id: str
    position: Position
    velocity: Velocity
    attributes: ParticleAttributes
    rules: ParticleRules
    speciesId: str
    color: str

# server/app/models/simulation.py

# [Previous imports and models remain the same until ParticleGroup]

class ParticleGroup(BaseModel):
    id: str
    memberIds: Set[str]
    speciesId: str
    parentIds: Optional[Set[str]]
    childId: Optional[str]

    class Config:
        json_encoders = {
            set: list  # Convert sets to lists during JSON serialization
        }

class Species(BaseModel):
    id: str
    name: str
    color: str
    baseRules: ParticleRules
    population: int = 0
    diet: Diet
    reproductionStyle: ReproductionStyle

class SimulationState(BaseModel):
    particles: Dict[str, Particle]
    species: Dict[str, Species]
    groups: Dict[str, ParticleGroup]
    worldWidth: int
    worldHeight: int
    tickCount: int = 0