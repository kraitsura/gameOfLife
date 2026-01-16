from app.simulation.core import Component, PHYSICS_CONFIG, Vector2D
from typing import TYPE_CHECKING, List, Optional
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
        from app.simulation.core.types import EntityType
        from app.simulation.models.entity import EntityState

        # Don't update if already dead
        if owner.state == EntityState.DEAD:
            return

        # Plants should not move at all - they stay at spawn position
        if owner.type == EntityType.PLANT:
            # Keep velocity at zero and reset any forces
            self.velocity = Vector2D(0, 0)
            self.acceleration = Vector2D(0, 0)
            owner.velocity = self.velocity
            return

        # FLEE BEHAVIOR (highest priority) - herbivores flee from predators
        threat = self._detect_nearby_threat(owner, context)
        if threat:
            # Calculate flee direction (away from threat)
            flee_direction = (owner.position - threat.position).normalize()
            # Strong flee force (2x normal max force)
            flee_force = flee_direction * PHYSICS_CONFIG["MAX_FORCE"] * 2.0
            self.apply_force(flee_force)
            # Skip wander when fleeing
        elif self.enable_wander and self.acceleration.magnitude() < 0.1:
            # Apply gentle wander force if enabled and no other forces present
            wander_force = self._calculate_wander_force(dt)
            self.apply_force(wander_force)

        # Apply flocking behaviors (Phase 2 optimization: batched queries)
        # Separation, cohesion, and alignment now share query results
        self._apply_flocking_forces(owner, context)

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

    def _apply_flocking_forces(self, owner: 'Entity', context: 'SimulationContext') -> None:
        """
        Apply all flocking forces using batched queries (Phase 2 optimization).

        Combines separation, cohesion, and alignment into a single query
        instead of 3 separate queries. This is the main optimization for
        reducing spatial query overhead.

        Args:
            owner: The entity
            context: Simulation context
        """
        from app.simulation.models import Entity
        from app.simulation.core.types import EntityType

        # Query once for the larger radius (vision range for cohesion/alignment)
        vision_range = owner.stats.entity_vision
        separation_radius = PHYSICS_CONFIG.get("SEPARATION_RADIUS", 15.0)

        # Use multi-radius query for optimal performance (Phase 2 optimization)
        nearby_by_radius = context.query_cache.get_nearby_multi_radius(
            owner.id,
            [separation_radius, vision_range],
            context
        )

        # Get results for each radius
        nearby_separation = nearby_by_radius[separation_radius]
        nearby_vision = nearby_by_radius[vision_range]

        # Calculate separation force
        separation_force = self._calculate_separation_force_from_list(owner, nearby_separation)
        if separation_force.magnitude() > 0:
            self.apply_force(separation_force)

        # Skip cohesion/alignment for plants
        if owner.type != EntityType.CREATURE:
            return

        # Filter to same species for cohesion and alignment
        same_species = [e for e in nearby_vision if isinstance(e, Entity) and e.species_id == owner.species_id]

        if not same_species:
            return

        # Calculate cohesion force
        cohesion_force = self._calculate_cohesion_force_from_list(owner, same_species)
        if cohesion_force.magnitude() > 0:
            self.apply_force(cohesion_force)

        # Calculate alignment force
        alignment_force = self._calculate_alignment_force_from_list(owner, same_species)
        if alignment_force.magnitude() > 0:
            self.apply_force(alignment_force)

    def _calculate_separation_force_from_list(self, owner: 'Entity', nearby: List['Entity']) -> Vector2D:
        """
        Calculate separation force from a pre-queried list (Phase 2 optimization).

        Args:
            owner: The entity
            nearby: Pre-queried nearby entities

        Returns:
            Separation steering force
        """
        from app.simulation.models import Entity

        separation_radius = PHYSICS_CONFIG.get("SEPARATION_RADIUS", 15.0)

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

    def _calculate_cohesion_force_from_list(self, owner: 'Entity', same_species: List['Entity']) -> Vector2D:
        """
        Calculate cohesion force from a pre-filtered list (Phase 2 optimization).

        Args:
            owner: The entity
            same_species: Pre-filtered same-species entities

        Returns:
            Cohesion steering force
        """
        if not same_species:
            return Vector2D(0, 0)

        # Calculate center of mass for same-species neighbors
        center_of_mass = Vector2D(0, 0)
        for neighbor in same_species:
            center_of_mass = center_of_mass + neighbor.position

        # Average position
        center_of_mass = center_of_mass * (1.0 / len(same_species))

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

    def _calculate_alignment_force_from_list(self, owner: 'Entity', same_species: List['Entity']) -> Vector2D:
        """
        Calculate alignment force from a pre-filtered list (Phase 2 optimization).

        Args:
            owner: The entity
            same_species: Pre-filtered same-species entities

        Returns:
            Alignment steering force
        """
        if not same_species:
            return Vector2D(0, 0)

        # Calculate average velocity for same-species neighbors
        avg_velocity = Vector2D(0, 0)
        for neighbor in same_species:
            avg_velocity = avg_velocity + neighbor.velocity

        # Average velocity
        avg_velocity = avg_velocity * (1.0 / len(same_species))

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

    def _detect_nearby_threat(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
        """
        Detect nearby predators for flee behavior (Phase 2: uses query cache).

        Herbivores flee from carnivores and omnivores.
        Only triggers for herbivores. Flee earlier if vulnerable (low health/energy).

        Args:
            owner: The entity checking for threats
            context: Simulation context

        Returns:
            Nearest threat entity or None
        """
        from app.simulation.models import Entity
        from app.simulation.core.types import Trait

        # Only herbivores flee
        if Trait.HERBIVORE not in owner.traits:
            return None

        # Check if entity is vulnerable (heightened fear)
        vitality = owner.get_component('VitalityComponent')
        is_vulnerable = False
        if vitality:
            is_vulnerable = (
                vitality.current_health < vitality.max_health * 0.5 or
                vitality.current_energy < vitality.max_energy * 0.3
            )

        # Search for predators within vision range (Phase 2: use query cache)
        detection_radius = owner.stats.entity_vision

        nearby = context.query_cache.get_nearby(
            owner.id,
            detection_radius,
            context
        )

        nearest_threat = None
        min_distance = float('inf')

        for entity in nearby:
            if not isinstance(entity, Entity):
                continue

            # Is this a predator?
            if Trait.CARNIVORE in entity.traits or Trait.OMNIVORE in entity.traits:
                distance = (owner.position - entity.position).magnitude()

                # Always flee if vulnerable, otherwise flee only if very close
                if is_vulnerable or distance < 30.0:
                    if distance < min_distance:
                        min_distance = distance
                        nearest_threat = entity

        return nearest_threat
