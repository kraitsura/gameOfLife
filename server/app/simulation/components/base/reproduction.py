from typing import TYPE_CHECKING, Optional
import random
import math
from app.simulation.core import Component, VITALITY_CONFIG, Vector2D

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class ReproductionComponent(Component):
    """Handles sexual reproduction between entities"""

    def __init__(self, reproduction_cooldown: float = 10.0):
        """
        Args:
            reproduction_cooldown: Seconds between reproduction attempts
        """
        self.reproduction_cooldown = reproduction_cooldown
        self.time_since_last_reproduction = reproduction_cooldown  # Can reproduce immediately if conditions met

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """Check for reproduction opportunities"""
        from app.simulation.models.entity import EntityState

        if owner.state == EntityState.DEAD:
            return

        # Increment cooldown timer
        self.time_since_last_reproduction += dt

        # Check if ready to reproduce
        if self.time_since_last_reproduction < self.reproduction_cooldown:
            return

        # Check energy threshold
        vitality = owner.get_component('VitalityComponent')
        if not vitality:
            return

        reproduction_threshold = VITALITY_CONFIG["REPRODUCTION_THRESHOLD"]
        if vitality.current_energy < reproduction_threshold:
            return

        # Find mate
        mate = self._find_compatible_mate(owner, context)
        if not mate:
            return

        # Reproduce!
        self._create_offspring(owner, mate, context)

        # Reset cooldowns and deduct energy
        self.time_since_last_reproduction = 0.0
        vitality.current_energy -= 40.0

        # Also reset mate's cooldown and energy
        mate_reproduction = mate.get_component('ReproductionComponent')
        mate_vitality = mate.get_component('VitalityComponent')
        if mate_reproduction:
            mate_reproduction.time_since_last_reproduction = 0.0
        if mate_vitality:
            mate_vitality.current_energy -= 40.0

    def _find_compatible_mate(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
        """Find nearby same-species entity that is also ready to reproduce"""
        from app.simulation.models import Entity
        from app.simulation.models.entity import EntityState

        # Search radius
        search_radius = 20.0

        # Query nearby entities
        nearby = context.query_nearby_entities(owner.position, search_radius, exclude_id=owner.id)

        for entity in nearby:
            # Must be same species
            if not isinstance(entity, Entity) or entity.species_id != owner.species_id:
                continue

            # Must be alive
            if entity.state == EntityState.DEAD:
                continue

            # Must have reproduction component
            mate_reproduction = entity.get_component('ReproductionComponent')
            if not mate_reproduction:
                continue

            # Must be ready (cooldown expired)
            if mate_reproduction.time_since_last_reproduction < mate_reproduction.reproduction_cooldown:
                continue

            # Must have enough energy
            mate_vitality = entity.get_component('VitalityComponent')
            if not mate_vitality:
                continue

            reproduction_threshold = VITALITY_CONFIG["REPRODUCTION_THRESHOLD"]
            if mate_vitality.current_energy < reproduction_threshold:
                continue

            # Found compatible mate!
            return entity

        return None

    def _create_offspring(self, parent1: 'Entity', parent2: 'Entity', context: 'SimulationContext') -> None:
        """Spawn child entity near parents"""
        from app.simulation.models import Species, Entity

        # Get parent's species
        species = context.get_by_id(Species, parent1.species_id)
        if not species:
            return

        # Calculate spawn position (random offset from parent1)
        angle = random.uniform(0, 2 * math.pi)
        offset_distance = 15.0
        offset = Vector2D(
            math.cos(angle) * offset_distance,
            math.sin(angle) * offset_distance
        )
        spawn_position = parent1.position + offset

        # Clamp to world bounds
        spawn_position.x = max(0, min(context.width, spawn_position.x))
        spawn_position.y = max(0, min(context.height, spawn_position.y))

        # Create offspring
        offspring = species.create_entity(spawn_position)

        # Register in simulation
        context.register(offspring)

        # Increment species population (create_entity already does this, but just to be safe)
        # Note: species.create_entity already increments population_count
