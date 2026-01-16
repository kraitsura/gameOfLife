from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Set, Optional, Any, TYPE_CHECKING, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from app.simulation.core.interfaces import GameObject, Component
from app.simulation.core.types import EntityType, Trait
from app.simulation.core.vector import Vector2D

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext

class EntityState(Enum):
    SPAWNING = auto()
    ACTIVE = auto()
    DORMANT = auto()
    DYING = auto()
    DEAD = auto()

@dataclass
class NetworkState:
    x: float
    y: float
    velocity_x: float
    velocity_y: float

@dataclass
class EntityStats:
    max_health: float = 100.0
    current_health: float = 100.0
    defense: float = 0.0
    attack: float = 0.0
    max_energy: float = 100.0
    current_energy: float = 100.0
    age: float = 0.0
    lifetime: float = float('inf')
    level: int = 1
    experience: float = 0.0
    experience_to_next_level: float = 100.0
    experience_decay_rate: float = 0.01
    entity_vision: float = 50.0  # Increased from 10.0 to match PHYSICS_CONFIG

class Entity(GameObject):
    def __init__(
        self,
        entity_type: EntityType,
        position: Vector2D,
        species_id: str,
        pack_id: Optional[str] = None,
        color: str = '#000000',
        size: float = 3.0,
        traits: Optional[Set[Trait]] = None,
        stats: Optional[EntityStats] = None
    ):
        self.id = str(uuid4())
        self.type = entity_type
        self.species_id = species_id
        self.pack_id = pack_id

        self.color = color
        self.size = size
        self.is_child = False

        self.position = position
        self.velocity = Vector2D(0, 0)

        self.state = EntityState.SPAWNING
        self.state_duration = 0.0

        self.stats = stats or EntityStats()
        self.traits = traits or set()
        self.components: Dict[str, Component] = {}

        # Collision data
        self.collision_mask = 0xFFFFFFFF  # Default to colliding with everything
        self.collision_layer = 0x00000001  # Default layer
        self.colliding_entities: Set[UUID] = set()

        # Spatial grid tracking (Phase 1 optimization)
        self._last_grid_cell: Optional[Tuple[int, int]] = None


    def update(self, context: 'SimulationContext', dt: float) -> None:
        """Update entity state and components"""
        current_time = datetime.now()
        self.stats.age += dt

        # Store previous position for physics/collision
        self.previous_position = Vector2D(self.position.x, self.position.y)

        # Update state duration
        self.state_duration += dt

        # Check lifetime
        if self.stats.age >= self.stats.lifetime:
            self.kill()

        # Update active effects
        self._update_effects(dt)

        # Handle state transitions
        if self.state == EntityState.SPAWNING and self.state_duration >= 1.0:
            self.set_state(EntityState.ACTIVE)

        # Update all components
        for component in self.components.values():
            component.update(self, context, dt)

        # Sync position from PhysicsComponent if it exists
        physics = self.get_component('PhysicsComponent')
        if physics:
            self.position = physics.position
            self.velocity = physics.velocity

        self.last_updated = current_time


    def add_component(self, component: Component) -> None:
        """Add a component to the entity"""
        name = component.__class__.__name__
        self.components[name] = component

    def remove_component(self, component_name: str) -> None:
        """Remove a component from the entity"""
        self.components.pop(component_name, None)

    def get_component(self, component_name: str) -> Optional[Component]:
        """Get a component by name"""
        return self.components.get(component_name)

    def has_component(self, component_name: str) -> bool:
        """Check if entity has a specific component"""
        return component_name in self.components

    def add_trait(self, trait: Trait) -> None:
        """Add a trait to the entity"""
        if trait not in self.traits:
            self.traits.add(trait)

    def remove_trait(self, trait: Trait) -> None:
        """Remove a trait from the entity"""
        if trait in self.traits:
            self.traits.remove(trait)

    def has_trait(self, trait: Trait) -> bool:
        """Check if entity has a specific trait"""
        return trait in self.traits

    def set_state(self, new_state: EntityState) -> None:
        """Change entity state"""
        if new_state != self.state:
            self.state = new_state
            self.state_duration = 0.0

    def kill(self) -> None:
        """Mark entity for removal"""
        self.set_state(EntityState.DEAD)

    def _update_effects(self, dt: float) -> None:
        """Update active effects (stub for now)"""
        pass

    def serialize(self) -> Dict[str, Any]:
        """Serialize entity to camelCase format for frontend compatibility"""
        return {
            'id': str(self.id),
            'speciesId': str(self.species_id),
            'packId': str(self.pack_id) if self.pack_id else None,
            'color': self.color,
            'size': self.size,
            'type': self.type.value,
            'x': self.position.x,
            'y': self.position.y,
            'vx': self.velocity.x,
            'vy': self.velocity.y,
            'energy': self.stats.current_energy,
            'health': self.stats.current_health,
            'visionRange': self.stats.entity_vision,
            'isChild': self.is_child,
        }
