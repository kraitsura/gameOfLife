from app.simulation.core import Component, PHYSICS_CONFIG, Vector2D
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class PhysicsComponent(Component):
    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        max_speed: float = PHYSICS_CONFIG["MAX_VELOCITY"],
        mass: float = 1.0
    ):
        self.position = position
        self.velocity = velocity
        self.acceleration = Vector2D(0, 0)
        self.max_speed = max_speed
        self.mass = mass

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        # Update velocity with acceleration
        self.velocity = self.velocity + (self.acceleration * dt)
        
        # Apply max speed limit
        speed = self.velocity.magnitude()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        
        # Update position
        self.position = self.position + (self.velocity * dt)
        
        # Wrap around world boundaries
        self.position.x = self.position.x % context.width
        self.position.y = self.position.y % context.height

        owner.velocity = self.velocity
        
        # Reset acceleration
        self.acceleration = Vector2D(0, 0)

    def apply_force(self, force: Vector2D) -> None:
        """Apply a force to the entity"""
        self.acceleration = self.acceleration + (force * (1.0 / self.mass))
