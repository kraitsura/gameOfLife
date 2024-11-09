from typing import Set
from app.simulation.core.types import EntityType, Trait
from app.simulation.models import Entity
from app.simulation.core import Vector2D

class ComponentFactory:
    @staticmethod
    def initialize_components(entity: 'Entity', traits: Set[Trait]) -> None:
        """Initialize all components for an entity based on its traits"""
        from app.simulation.components.base import (
            PhysicsComponent,
            VitalityComponent,
            SocialComponent,
            ReproductionComponent
        )
        from app.simulation.components.diet import (
            HerbivoreComponent,
            CarnivoreComponent,
            OmnivoreComponent
        )

        # Add basic components
        entity.add_component(PhysicsComponent(position=entity.position, velocity=Vector2D(0, 0)))
        entity.add_component(VitalityComponent())
        
        # Add creature-specific components
        if entity.type == EntityType.CREATURE:
            entity.add_component(SocialComponent())
            entity.add_component(ReproductionComponent(
                style="two_parents" if Trait.TWO_PARENTS in traits else "self_replicating"
            ))
        
        # Add diet components
        if Trait.HERBIVORE in traits:
            entity.add_component(HerbivoreComponent())
        elif Trait.CARNIVORE in traits:
            entity.add_component(CarnivoreComponent())
        elif Trait.OMNIVORE in traits:
            entity.add_component(OmnivoreComponent())