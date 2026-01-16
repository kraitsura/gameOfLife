from typing import Set
import random
import math
from app.simulation.core.types import EntityType, Trait
from app.simulation.models import Entity
from app.simulation.core import Vector2D

class ComponentFactory:
    @staticmethod
    def initialize_components(entity: 'Entity', traits: Set[Trait]) -> None:
        """Initialize all components for an entity based on its traits"""
        from app.simulation.components.base.physics import PhysicsComponent
        from app.simulation.components.base.vitality import VitalityComponent
        from app.simulation.components.base.diet import DietComponent

        # Add basic components with random velocity for creatures
        if entity.type == EntityType.CREATURE:
            # Species-specific speed based on traits
            if Trait.HERBIVORE in traits:
                max_speed = 15.0
                speed = random.uniform(12.0, 15.0)
            elif Trait.CARNIVORE in traits:
                max_speed = 8.0
                speed = random.uniform(6.0, 8.0)
            elif Trait.OMNIVORE in traits:
                max_speed = 12.0
                speed = random.uniform(10.0, 12.0)
            else:
                max_speed = 10.0  # Default
                speed = random.uniform(8.0, 10.0)

            # Random starting direction
            angle = random.uniform(0, 2 * math.pi)
            velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
            enable_wander = True
        else:
            # Plants don't move (but still have physics for position tracking)
            velocity = Vector2D(0, 0)
            max_speed = 0.0
            enable_wander = False

        entity.add_component(PhysicsComponent(
            position=entity.position,
            velocity=velocity,
            max_speed=max_speed,
            enable_wander=enable_wander
        ))
        entity.add_component(VitalityComponent())

        # Add diet component for creatures with diet traits
        if entity.type == EntityType.CREATURE:
            diet_trait = None
            if Trait.HERBIVORE in traits:
                diet_trait = Trait.HERBIVORE
            elif Trait.CARNIVORE in traits:
                diet_trait = Trait.CARNIVORE
            elif Trait.OMNIVORE in traits:
                diet_trait = Trait.OMNIVORE

            if diet_trait:
                entity.add_component(DietComponent(diet_trait=diet_trait))

            # Add social component for pack formation (creatures only)
            from app.simulation.components.base.social import SocialComponent
            entity.add_component(SocialComponent())

        # Add ReproductionComponent
        from app.simulation.components.base.reproduction import ReproductionComponent
        if entity.type == EntityType.CREATURE and Trait.TWO_PARENTS in traits:
            entity.add_component(ReproductionComponent(reproduction_cooldown=10.0))
        elif entity.type == EntityType.PLANT and Trait.SELF_REPLICATING in traits:
            # Plants reproduce asexually (shorter cooldown)
            entity.add_component(ReproductionComponent(reproduction_cooldown=5.0))