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
            # Random starting velocity for movement
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.0, 3.0)
            velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
            enable_wander = True
        else:
            # Plants don't move (but still have physics for position tracking)
            velocity = Vector2D(0, 0)
            enable_wander = False

        entity.add_component(PhysicsComponent(
            position=entity.position,
            velocity=velocity,
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

        # TODO: Add SocialComponent and ReproductionComponent in future phases