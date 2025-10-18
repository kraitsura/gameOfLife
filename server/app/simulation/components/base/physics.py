from app.simulation.core import Component, PHYSICS_CONFIG, Vector2D
from typing import TYPE_CHECKING, List
import random
import math

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class PhysicsComponent(Component):
    """
    Handles entity movement with steering forces and boid-like behaviors.

    Supports multiple steering behaviors:
    - Seeking/fleeing targets
    - Separation from neighbors
    - Cohesion with group
    - Random wandering
    - Boundary wrapping
    """

    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        max_speed: float = PHYSICS_CONFIG["MAX_VELOCITY"],
        mass: float = 1.0,
        enable_wander: bool = True
    ):
        self.position = position
        self.velocity = velocity
        self.acceleration = Vector2D(0, 0)
        self.max_speed = max_speed
        self.mass = mass

        # Wander behavior
        self.enable_wander = enable_wander
        self.wander_angle = random.uniform(0, math.pi * 2)
        self.wander_timer = 0.0

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """
        Update physics each frame.

        Other components apply forces via apply_force().
        This component integrates forces into velocity and position.
        """
        # Apply gentle wander force if enabled and no other forces present
        if self.enable_wander and self.acceleration.magnitude() < 0.1:
            wander_force = self._calculate_wander_force(dt)
            self.apply_force(wander_force)

        # Apply flocking behaviors (separation, cohesion, alignment)
        separation_force = self._calculate_separation_force(owner, context)
        if separation_force.magnitude() > 0:
            self.apply_force(separation_force)

        cohesion_force = self._calculate_cohesion_force(owner, context)
        if cohesion_force.magnitude() > 0:
            self.apply_force(cohesion_force)

        alignment_force = self._calculate_alignment_force(owner, context)
        if alignment_force.magnitude() > 0:
            self.apply_force(alignment_force)

        # Update velocity with acceleration
        self.velocity = self.velocity + (self.acceleration * dt)

        # Apply friction
        friction = PHYSICS_CONFIG.get("FRICTION", 0.1)
        self.velocity = self.velocity * (1.0 - friction * dt)

        # Apply max speed limit
        speed = self.velocity.magnitude()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Ensure minimum speed (prevent getting stuck)
        if speed > 0 and speed < 0.5:
            self.velocity = self.velocity.normalize() * 0.5

        # Update position
        self.position = self.position + (self.velocity * dt)

        # Handle wall collisions with bouncing
        bounced = False

        # Check X boundaries
        if self.position.x < 0:
            self.position.x = 0
            self.velocity.x = abs(self.velocity.x)  # Bounce right
            bounced = True
        elif self.position.x > context.width:
            self.position.x = context.width
            self.velocity.x = -abs(self.velocity.x)  # Bounce left
            bounced = True

        # Check Y boundaries
        if self.position.y < 0:
            self.position.y = 0
            self.velocity.y = abs(self.velocity.y)  # Bounce down
            bounced = True
        elif self.position.y > context.height:
            self.position.y = context.height
            self.velocity.y = -abs(self.velocity.y)  # Bounce up
            bounced = True

        # Apply slight damping on bounce to prevent infinite bouncing
        if bounced:
            damping = PHYSICS_CONFIG.get("BOUNCE_DAMPING", 0.8)
            self.velocity = self.velocity * damping

        # Sync with entity
        owner.velocity = self.velocity

        # Reset acceleration for next frame
        self.acceleration = Vector2D(0, 0)

    def apply_force(self, force: Vector2D) -> None:
        """
        Apply a force to the entity.

        Args:
            force: Force vector to apply
        """
        # F = ma, so a = F/m
        self.acceleration = self.acceleration + (force * (1.0 / self.mass))

    def _calculate_wander_force(self, dt: float) -> Vector2D:
        """
        Calculate gentle random wander force.

        Uses a wandering angle that changes gradually for smooth movement.

        Args:
            dt: Delta time

        Returns:
            Wander steering force
        """
        # Update wander angle periodically
        self.wander_timer += dt
        if self.wander_timer > 1.0:  # Change direction every second
            # Small random change to wander angle
            self.wander_angle += random.uniform(-math.pi / 6, math.pi / 6)
            self.wander_timer = 0.0

        # Calculate wander direction
        wander_direction = Vector2D(
            math.cos(self.wander_angle),
            math.sin(self.wander_angle)
        )

        # Weak wander force (easily overridden by other behaviors)
        wander_strength = PHYSICS_CONFIG.get("WANDER_STRENGTH", 2.0)
        return wander_direction * wander_strength

    def _calculate_separation_force(self, owner: 'Entity', context: 'SimulationContext') -> Vector2D:
        """
        Calculate separation force to avoid crowding neighbors.

        Args:
            owner: The entity
            context: Simulation context

        Returns:
            Separation steering force
        """
        from app.simulation.models import Entity

        separation_radius = PHYSICS_CONFIG.get("SEPARATION_RADIUS", 15.0)

        # Query nearby entities
        nearby = context.query_nearby_entities(
            owner.position,
            separation_radius,
            exclude_id=owner.id
        )

        if not nearby:
            return Vector2D(0, 0)

        # Calculate average repulsion from neighbors
        repulsion = Vector2D(0, 0)
        count = 0

        for neighbor in nearby:
            if not isinstance(neighbor, Entity):
                continue

            distance = (neighbor.position - owner.position).magnitude()
            if distance > 0 and distance < separation_radius:
                # Repulsion inversely proportional to distance
                diff = owner.position - neighbor.position
                diff = diff.normalize()
                diff = diff * (1.0 / distance)  # Closer = stronger repulsion
                repulsion = repulsion + diff
                count += 1

        if count > 0:
            repulsion = repulsion * (1.0 / count)  # Average

            # Scale to max force
            if repulsion.magnitude() > 0:
                max_force = PHYSICS_CONFIG.get("MAX_FORCE", 5.0)
                repulsion = repulsion.normalize() * (max_force * 0.5)  # Half strength

        return repulsion

    def _calculate_cohesion_force(self, owner: 'Entity', context: 'SimulationContext') -> Vector2D:
        """
        Calculate cohesion force to move toward the center of nearby same-species entities.

        Args:
            owner: The entity
            context: Simulation context

        Returns:
            Cohesion steering force
        """
        from app.simulation.models import Entity
        from app.simulation.core.types import EntityType

        # Only apply cohesion to creatures
        if owner.type != EntityType.CREATURE:
            return Vector2D(0, 0)

        # Use vision range for cohesion (match old server behavior)
        vision_range = owner.stats.entity_vision

        # Query nearby entities
        nearby = context.query_nearby_entities(
            owner.position,
            vision_range,
            exclude_id=owner.id
        )

        if not nearby:
            return Vector2D(0, 0)

        # Calculate center of mass for same-species neighbors
        center_of_mass = Vector2D(0, 0)
        count = 0

        for neighbor in nearby:
            if not isinstance(neighbor, Entity):
                continue

            # Only cohesion with same species
            if neighbor.species_id == owner.species_id:
                center_of_mass = center_of_mass + neighbor.position
                count += 1

        if count == 0:
            return Vector2D(0, 0)

        # Average position
        center_of_mass = center_of_mass * (1.0 / count)

        # Steer toward center of mass
        desired = center_of_mass - owner.position

        if desired.magnitude() > 0:
            desired = desired.normalize() * self.max_speed
            steer = desired - self.velocity

            # Limit to max force (weaker than separation)
            max_force = PHYSICS_CONFIG.get("MAX_FORCE", 5.0)
            if steer.magnitude() > max_force * 0.3:
                steer = steer.normalize() * (max_force * 0.3)

            return steer

        return Vector2D(0, 0)

    def _calculate_alignment_force(self, owner: 'Entity', context: 'SimulationContext') -> Vector2D:
        """
        Calculate alignment force to match velocity with nearby same-species entities.

        Args:
            owner: The entity
            context: Simulation context

        Returns:
            Alignment steering force
        """
        from app.simulation.models import Entity
        from app.simulation.core.types import EntityType

        # Only apply alignment to creatures
        if owner.type != EntityType.CREATURE:
            return Vector2D(0, 0)

        # Use vision range for alignment (match old server behavior)
        vision_range = owner.stats.entity_vision

        # Query nearby entities
        nearby = context.query_nearby_entities(
            owner.position,
            vision_range,
            exclude_id=owner.id
        )

        if not nearby:
            return Vector2D(0, 0)

        # Calculate average velocity for same-species neighbors
        avg_velocity = Vector2D(0, 0)
        count = 0

        for neighbor in nearby:
            if not isinstance(neighbor, Entity):
                continue

            # Only align with same species
            if neighbor.species_id == owner.species_id:
                avg_velocity = avg_velocity + neighbor.velocity
                count += 1

        if count == 0:
            return Vector2D(0, 0)

        # Average velocity
        avg_velocity = avg_velocity * (1.0 / count)

        # Steer toward average velocity
        if avg_velocity.magnitude() > 0:
            desired = avg_velocity.normalize() * self.max_speed
            steer = desired - self.velocity

            # Limit to max force (weaker than separation)
            max_force = PHYSICS_CONFIG.get("MAX_FORCE", 5.0)
            if steer.magnitude() > max_force * 0.3:
                steer = steer.normalize() * (max_force * 0.3)

            return steer

        return Vector2D(0, 0)
