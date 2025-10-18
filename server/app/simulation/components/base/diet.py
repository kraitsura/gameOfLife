"""
Diet Component - Handles food seeking and consumption behavior.

Entities with this component will search for food using the spatial grid
and apply steering forces to move toward food sources.
"""

from app.simulation.core import Component, Trait, EntityType, PHYSICS_CONFIG
from app.simulation.core.vector import Vector2D
from typing import TYPE_CHECKING, Optional
import logging

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext


class DietComponent(Component):
    """
    Handles food-seeking behavior based on diet trait.

    - Herbivores seek plants
    - Carnivores seek other creatures
    - Omnivores seek both

    Uses spatial grid to efficiently find food within vision range,
    then applies steering forces to move toward the nearest food source.
    """

    def __init__(self, diet_trait: Trait, vision_range: float = None):
        """
        Initialize the diet component.

        Args:
            diet_trait: The diet trait (HERBIVORE, CARNIVORE, or OMNIVORE)
            vision_range: How far the entity can see food (defaults to PHYSICS_CONFIG)
        """
        if diet_trait not in {Trait.HERBIVORE, Trait.CARNIVORE, Trait.OMNIVORE}:
            raise ValueError(f"Invalid diet trait: {diet_trait}")

        self.diet_trait = diet_trait
        self.vision_range = vision_range or PHYSICS_CONFIG["VISION_RANGE"]
        self.hunger_level = 0.0  # Increases over time, decreases when eating
        self.target_food_id: Optional[str] = None  # Current food target

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """
        Update food-seeking behavior.

        1. Query spatial grid for food within vision range
        2. Filter by diet preferences
        3. Find nearest food
        4. Apply steering force toward food
        5. Consume food on contact
        6. If no food and wall detected, turn away from wall
        """
        # Increase hunger over time
        self.hunger_level += dt * 0.1

        # Find food using spatial grid
        food_target = self._find_nearest_food(owner, context)

        if food_target:
            self.target_food_id = food_target.id
            # Apply steering force toward food
            steering_force = self._calculate_seeking_force(owner, food_target)

            # Apply force to physics component
            physics = owner.get_component('PhysicsComponent')
            if physics:
                physics.apply_force(steering_force)

            # Check if close enough to consume
            distance = (food_target.position - owner.position).magnitude()
            if distance < PHYSICS_CONFIG["INTERACTION_RANGE"]:
                self._consume_food(owner, food_target, context)
        else:
            self.target_food_id = None

            # No food found - check for walls and avoid them
            wall_avoidance_force = self._calculate_wall_avoidance(owner, context)
            if wall_avoidance_force.magnitude() > 0:
                physics = owner.get_component('PhysicsComponent')
                if physics:
                    physics.apply_force(wall_avoidance_force)

    def _find_nearest_food(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
        """
        Find the nearest food entity within vision range.

        Args:
            owner: The entity searching for food
            context: Simulation context with spatial grid

        Returns:
            Nearest food entity or None if no food found
        """
        from app.simulation.models import Entity

        # Query nearby entities using spatial grid
        nearby_entities = context.query_nearby_entities(
            owner.position,
            self.vision_range,
            exclude_id=owner.id
        )

        # Filter by diet preferences
        food_candidates = []
        for entity in nearby_entities:
            if not isinstance(entity, Entity):
                continue

            # Check if this entity is food for us
            if self._is_food(entity, owner):
                food_candidates.append(entity)

        if not food_candidates:
            return None

        # Find nearest food
        nearest_food = None
        min_distance = float('inf')

        for food in food_candidates:
            distance = (food.position - owner.position).magnitude()
            if distance < min_distance:
                min_distance = distance
                nearest_food = food

        return nearest_food

    def _is_food(self, target: 'Entity', owner: 'Entity') -> bool:
        """
        Check if target entity is edible based on diet.

        Args:
            target: Potential food entity
            owner: The hungry entity

        Returns:
            True if target is food for owner
        """
        if self.diet_trait == Trait.HERBIVORE:
            # Herbivores eat plants
            return target.type == EntityType.PLANT

        elif self.diet_trait == Trait.CARNIVORE:
            # Carnivores eat other creatures (not same species, not self)
            return (target.type == EntityType.CREATURE and
                    target.species_id != owner.species_id)

        elif self.diet_trait == Trait.OMNIVORE:
            # Omnivores eat plants and other creatures
            if target.type == EntityType.PLANT:
                return True
            if target.type == EntityType.CREATURE and target.species_id != owner.species_id:
                return True

        return False

    def _calculate_seeking_force(self, owner: 'Entity', target: 'Entity') -> Vector2D:
        """
        Calculate steering force to move toward food.

        Uses Reynolds steering behavior: desired velocity - current velocity

        Args:
            owner: The seeking entity
            target: The food target

        Returns:
            Steering force vector
        """
        # Desired velocity: move toward target at max speed
        desired = (target.position - owner.position).normalize()
        desired = desired * PHYSICS_CONFIG["MAX_VELOCITY"]

        # Steering force: desired - current
        physics = owner.get_component('PhysicsComponent')
        if physics:
            steering = desired - physics.velocity
            # Limit to max force
            if steering.magnitude() > PHYSICS_CONFIG["MAX_FORCE"]:
                steering = steering.normalize() * PHYSICS_CONFIG["MAX_FORCE"]
            return steering

        return Vector2D(0, 0)

    def _consume_food(self, owner: 'Entity', food: 'Entity', context: 'SimulationContext') -> None:
        """
        Consume food entity and gain energy.

        Args:
            owner: The eating entity
            food: The food entity
            context: Simulation context
        """
        # Determine energy gained based on food type
        if food.type == EntityType.PLANT:
            energy_gained = 15.0
        else:  # CREATURE
            energy_gained = 30.0  # Meat is more nutritious

        # Restore energy via VitalityComponent
        vitality = owner.get_component('VitalityComponent')
        if vitality:
            actual_gained = vitality.restore_energy(energy_gained)
            logging.debug(f"Entity {owner.id} consumed {food.type.value}, gained {actual_gained:.1f} energy")

        # Reduce hunger
        self.hunger_level = max(0.0, self.hunger_level - 50.0)

        # Remove food entity (plants regenerate, creatures die)
        if food.type == EntityType.PLANT:
            # Plant respawns elsewhere (handled by plant system)
            # For now, just mark as dead
            food.kill()
        elif food.type == EntityType.CREATURE:
            # Creature is killed
            food.kill()

        self.target_food_id = None

    def _detect_wall_in_vision(self, owner: 'Entity', context: 'SimulationContext') -> Optional[str]:
        """
        Detect if a wall is visible within vision range.

        Args:
            owner: The entity checking for walls
            context: Simulation context with world bounds

        Returns:
            Wall direction ('left', 'right', 'top', 'bottom') or None
        """
        pos = owner.position
        vision = self.vision_range

        # Check each wall - return the closest one within vision
        distances = []

        # Left wall (x = 0)
        if pos.x < vision:
            distances.append(('left', pos.x))

        # Right wall (x = width)
        if context.width - pos.x < vision:
            distances.append(('right', context.width - pos.x))

        # Top wall (y = 0)
        if pos.y < vision:
            distances.append(('top', pos.y))

        # Bottom wall (y = height)
        if context.height - pos.y < vision:
            distances.append(('bottom', context.height - pos.y))

        if not distances:
            return None

        # Return closest wall
        closest_wall = min(distances, key=lambda x: x[1])
        return closest_wall[0]

    def _calculate_wall_avoidance(self, owner: 'Entity', context: 'SimulationContext') -> Vector2D:
        """
        Calculate steering force to turn away from nearby walls.

        When no food is visible and a wall is detected, apply a force
        that steers the entity away from the wall.

        Args:
            owner: The entity avoiding walls
            context: Simulation context

        Returns:
            Wall avoidance steering force
        """
        wall_direction = self._detect_wall_in_vision(owner, context)

        if wall_direction is None:
            return Vector2D(0, 0)

        pos = owner.position

        # Calculate direction away from wall
        avoidance_direction = Vector2D(0, 0)

        if wall_direction == 'left':
            # Wall on left, push right
            distance_to_wall = pos.x
            avoidance_direction = Vector2D(1, 0)
        elif wall_direction == 'right':
            # Wall on right, push left
            distance_to_wall = context.width - pos.x
            avoidance_direction = Vector2D(-1, 0)
        elif wall_direction == 'top':
            # Wall on top, push down
            distance_to_wall = pos.y
            avoidance_direction = Vector2D(0, 1)
        elif wall_direction == 'bottom':
            # Wall on bottom, push up
            distance_to_wall = context.height - pos.y
            avoidance_direction = Vector2D(0, -1)
        else:
            return Vector2D(0, 0)

        # Strength inversely proportional to distance
        # Closer to wall = stronger avoidance
        strength = PHYSICS_CONFIG["MAX_FORCE"] * (1.0 - (distance_to_wall / self.vision_range))
        strength = max(strength, PHYSICS_CONFIG["MAX_FORCE"] * 0.3)  # Minimum strength

        return avoidance_direction * strength
