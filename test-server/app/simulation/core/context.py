from typing import Dict, List, Optional, TypeVar, Type
from uuid import UUID
from app.simulation.core.interfaces import GameObject

T = TypeVar('T', bound=GameObject)

class SimulationContext:
    """
    Context object that provides access to simulation state and services.
    This breaks circular dependencies by being passed to objects that need
    access to simulation state.
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._objects: Dict[UUID, GameObject] = {}
        self._object_types: Dict[Type[GameObject], List[UUID]] = {}
        self.time: float = 0.0
        self.tick_rate: int = 0

    def register(self, obj: GameObject) -> None:
        """Register a game object with the simulation"""
        self._objects[obj.id] = obj
        obj_type = type(obj)
        if obj_type not in self._object_types:
            self._object_types[obj_type] = []
        self._object_types[obj_type].append(obj.id)

    def unregister(self, obj: GameObject) -> None:
        """Remove a game object from the simulation"""
        if obj.id in self._objects:
            del self._objects[obj.id]
            obj_type = type(obj)
            if obj_type in self._object_types:
                self._object_types[obj_type].remove(obj.id)

    def get_object(self, obj_id: UUID) -> Optional[GameObject]:
        """Get an object by its ID"""
        return self._objects.get(obj_id)

    def get_objects_by_type(self, obj_type: Type[T]) -> List[T]:
        """Get all objects of a specific type"""
        if obj_type not in self._object_types:
            return []
        return [self._objects[obj_id] for obj_id in self._object_types[obj_type]]

    def update(self, dt: float) -> None:
        """Update all objects in the simulation"""
        self.time += dt
        # Create a copy of values to allow for object removal during iteration
        for obj in list(self._objects.values()):
            obj.update(self, dt)