from typing import Protocol, runtime_checkable, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext

@runtime_checkable
class GameObject(Protocol):
    """Base interface for all game objects"""
    id: UUID
    
    def update(self, context: 'SimulationContext', dt: float) -> None: ...
    def serialize(self) -> dict: ...
    @classmethod
    def deserialize(cls, data: dict) -> 'GameObject':
        return cls(**data)

@runtime_checkable
class Component(Protocol):
    """Base interface for all components"""
    def update(self, owner: GameObject, context: 'SimulationContext', dt: float) -> None:
        pass
        
    def serialize(self) -> dict:
        pass
    
    @classmethod
    def deserialize(cls, data: dict) -> 'Component':
        return cls(**data)
