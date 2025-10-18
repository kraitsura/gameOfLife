from app.simulation.core import Component, VITALITY_CONFIG
from typing import Set
from app.simulation.models import Entity
from app.simulation.core.context import SimulationContext

class ReproductionComponent(Component):
    def __init__(
        self,
        style: str,
        maturity_age: int = 100,
        reproduction_cooldown: int = 200
    ):
        self.style = style
        self.maturity_age = maturity_age
        self.reproduction_cooldown = reproduction_cooldown
        self.last_reproduced = 0
        self.offspring_count = 0
        self.parent_ids: Set[str] = set()
        self.is_pregnant = False
        self.gestation_time = 0
        self.max_gestation = 100

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        self.last_reproduced += 1
        
        if self.is_pregnant:
            self.gestation_time += 1
            if self.gestation_time >= self.max_gestation:
                self._give_birth(owner, context.world)

    def can_reproduce(self, entity: 'Entity') -> bool:
        return (
            entity.vitality.age >= self.maturity_age and
            entity.vitality.energy >= VITALITY_CONFIG["REPRODUCTION_THRESHOLD"] and
            self.last_reproduced >= self.reproduction_cooldown and
            not self.is_pregnant
        )

    def _give_birth(self, owner: 'Entity', world: 'SimulationContext') -> None:
        # Implementation for birth process
        self.is_pregnant = False
        self.gestation_time = 0
        self.offspring_count += 1