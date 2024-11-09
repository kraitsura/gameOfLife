from app.simulation.core import Component, VITALITY_CONFIG
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class VitalityComponent(Component):
    def __init__(
        self,
        energy: float = VITALITY_CONFIG["BASE_ENERGY"],
        hunger: float = 0.0,
        size: float = 3.0
    ):
        self.energy = energy
        self.hunger = hunger
        self.size = size
        self.age = 0
        self.last_ate = 0
        self.health = 100.0

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        self.age += 1
        self.last_ate += 1
        
        # Basic metabolism
        self.energy -= VITALITY_CONFIG["ENERGY_DECAY_RATE"] * dt
        self.hunger += VITALITY_CONFIG["HUNGER_RATE"] * dt
        
        # Health effects
        if self.hunger > 75:
            self.health -= 0.1 * dt
        if self.energy < 25:
            self.health -= 0.1 * dt
            
        # Cap values
        self.energy = max(0, min(100, self.energy))
        self.hunger = max(0, min(100, self.hunger))
        self.health = max(0, min(100, self.health))
