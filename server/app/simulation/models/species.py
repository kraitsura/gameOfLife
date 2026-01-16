from typing import Set, TYPE_CHECKING
from uuid import uuid4
from app.simulation.core.types import EntityType, Trait
from app.simulation.core.vector import Vector2D
from app.simulation.models import Entity
from app.simulation.models.entity import EntityStats
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

    def get_base_stats(self) -> EntityStats:
        """Return species-specific base stats based on traits

        Design philosophy:
        - Herbivores: Fast, fragile, good vision (spot predators early)
        - Carnivores: Strong, tanky, slower (persistence hunters)
        - Omnivores: Balanced (Jack of all trades)
        - Plants: Stationary, fragile, quick respawn
        """
        if Trait.HERBIVORE in self.base_traits:
            return EntityStats(
                max_health=80.0,
                current_health=80.0,
                defense=2.0,
                attack=1.0,
                max_energy=120.0,
                current_energy=120.0,
                entity_vision=70.0,
                lifetime=float('inf')
            )

        elif Trait.CARNIVORE in self.base_traits:
            return EntityStats(
                max_health=120.0,
                current_health=120.0,
                defense=5.0,
                attack=10.0,
                max_energy=100.0,
                current_energy=100.0,
                entity_vision=60.0,
                lifetime=float('inf')
            )

        elif Trait.OMNIVORE in self.base_traits:
            return EntityStats(
                max_health=100.0,
                current_health=100.0,
                defense=3.0,
                attack=5.0,
                max_energy=110.0,
                current_energy=110.0,
                entity_vision=65.0,
                lifetime=float('inf')
            )

        elif Trait.SELF_REPLICATING in self.base_traits:  # Plants
            return EntityStats(
                max_health=30.0,
                current_health=30.0,
                defense=0.0,
                attack=0.0,
                max_energy=0.0,
                current_energy=0.0,
                entity_vision=0.0,
                lifetime=600.0  # 10 seconds at 60 FPS
            )

        else:
            # Default fallback
            return EntityStats()

    def create_entity(self, position: Vector2D) -> 'Entity':
        """Factory method to create new entities of this species"""
        # Get species-specific stats
        stats = self.get_base_stats()

        entity = Entity(
            entity_type=self.type,
            position=position,
            species_id=self.id,
            color=self.color,
            traits=self.base_traits.copy(),
            stats=stats  # Use species-specific stats
        )

        # Component initialization
        from app.simulation.factory.component_factory import ComponentFactory
        ComponentFactory.initialize_components(entity, self.base_traits)

        self.population += 1
        self.total_spawned += 1
        return entity
    
    def update(self, context: 'SimulationContext', dt: float) -> None:
        """
        Update species-level state.

        Note: Individual entities are updated by SimulationContext.update() directly.
        This method should only handle species-level aggregations or behaviors.
        Previously, this method iterated through entities and updated them, causing
        double updates since entities are already updated by the context.
        """
        # Species-level update logic can go here if needed in the future
        # For now, no additional processing is required
        pass

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "color": self.color,
            "traits": [trait.value for trait in self.base_traits],
            "population": self.population,
        }