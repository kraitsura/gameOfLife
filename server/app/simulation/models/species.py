from typing import Set, TYPE_CHECKING
from uuid import uuid4
from app.simulation.core.types import EntityType, Trait
from app.simulation.core.vector import Vector2D
from app.simulation.models import Entity
from app.simulation.core.interfaces import GameObject

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext

class Species(GameObject):
    def __init__(
        self,
        name: str,
        entity_type: EntityType,
        color: str,
        base_traits: Set[Trait],
        initial_population: int = 10
    ):
        self.id = str(uuid4())
        self.name = name
        self.type = entity_type
        self.color = color
        self.base_traits = base_traits
        self.population = 0  # Will be incremented as entities are created
        self.total_spawned = 0
        self.generation = 0

    def create_entity(self, position: Vector2D) -> 'Entity':
        """Factory method to create new entities of this species"""
        entity = Entity(
            entity_type=self.type,
            position=position,
            species_id=self.id,
            color=self.color,
            traits=self.base_traits.copy()
        )

        # Component initialization
        from app.simulation.factory.component_factory import ComponentFactory
        ComponentFactory.initialize_components(entity, self.base_traits)

        self.population += 1
        self.total_spawned += 1
        return entity
    
    def update(self, context: 'SimulationContext', dt: float) -> None:
        for entity in context.get_objects_by_type(Entity):
            if entity.species_id == self.id:
                entity.update(context, dt)
        

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "color": self.color,
            "traits": [trait.value for trait in self.base_traits],
            "population": self.population,
        }