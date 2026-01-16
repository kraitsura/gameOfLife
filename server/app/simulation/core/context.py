import logging
from typing import Dict, List, Optional, TypeVar, Type
from app.simulation.core.interfaces import GameObject
from app.simulation.core.spatial_grid import SpatialGrid
from app.simulation.core.query_cache import FrameQueryCache
from app.simulation.core.config import GRID_CONFIG
from app.simulation.core.vector import Vector2D

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
        self._objects: Dict[str, GameObject] = {}
        self._object_types: Dict[Type[GameObject], List[str]] = {}
        self.time: float = 0.0
        self.tick_rate: int = 0

        # Spatial grid for efficient neighbor queries
        self.spatial_grid = SpatialGrid(
            world_width=width,
            world_height=height,
            cell_size=GRID_CONFIG["CELL_SIZE"]
        )

        # Query cache for reducing redundant spatial queries (Phase 2 optimization)
        self.query_cache = FrameQueryCache()

    def register(self, obj: GameObject) -> None:
        """Register a game object with the simulation"""
        from app.simulation.models.entity import Entity

        try:
            self._objects[obj.id] = obj
            obj_type = type(obj)
            if obj_type not in self._object_types:
                self._object_types[obj_type] = []
            self._object_types[obj_type].append(obj.id)

            # Add entity to spatial grid immediately (Phase 1 optimization)
            if isinstance(obj, Entity):
                self.spatial_grid.insert(obj.id, obj.position)
                obj._last_grid_cell = self.spatial_grid._get_cell_coords(obj.position)
        except Exception as e:
            logging.error("Failed to register object '%s': %s", obj.id, str(e))
            raise

    def unregister(self, obj: GameObject) -> None:
        """Remove a game object from the simulation"""
        from app.simulation.models.entity import Entity

        if obj.id in self._objects:
            # Remove entity from spatial grid (Phase 1 optimization)
            if isinstance(obj, Entity):
                self.spatial_grid.remove(obj.id)
                obj._last_grid_cell = None

            del self._objects[obj.id]
            obj_type = type(obj)
            if obj_type in self._object_types:
                self._object_types[obj_type].remove(obj.id)

    def get_object(self, obj_id: str) -> Optional[GameObject]:
        """Get an object by its ID"""
        return self._objects.get(obj_id)

    def get_objects_by_type(self, obj_type: Type[T]) -> List[T]:
        """Get all objects of a specific type"""
        if obj_type not in self._object_types:
            return []
        return [self._objects[obj_id] for obj_id in self._object_types[obj_type]]
    
    def get_by_id(self, obj_type: Type[T], obj_id: str) -> Optional[T]:
        """Get an object of specific type by ID"""
        if obj_id in self._objects:
            obj = self._objects[obj_id]
            if isinstance(obj, obj_type):
                return obj
        return None

    def update(self, dt: float) -> None:
        """Update all objects in the simulation"""
        self.time += dt

        # Invalidate query cache for new frame (Phase 2 optimization)
        self.query_cache.new_frame()

        # Update spatial grid incrementally before entity updates (Phase 1 optimization)
        self._update_spatial_grid_incremental()

        # Create a copy of values to allow for object removal during iteration
        for obj in list(self._objects.values()):
            obj.update(self, dt)

        # Cleanup dead entities after updates
        self._cleanup_dead_entities()

    def _update_spatial_grid_incremental(self) -> None:
        """
        Incrementally update the spatial grid (Phase 1 optimization).
        Only updates entities that have changed grid cells.
        This is O(k) where k = entities that moved, instead of O(n) rebuild.
        """
        from app.simulation.models.entity import Entity

        entities = self.get_objects_by_type(Entity)
        for entity in entities:
            current_cell = self.spatial_grid._get_cell_coords(entity.position)

            # Check if entity changed cells
            if entity._last_grid_cell != current_cell:
                # Remove from old cell if it was tracked
                if entity._last_grid_cell is not None:
                    # Use the spatial grid's remove method
                    self.spatial_grid.remove(entity.id)

                # Insert into new cell
                self.spatial_grid.insert(entity.id, entity.position)

                # Update tracked cell
                entity._last_grid_cell = current_cell

    def _rebuild_spatial_grid(self) -> None:
        """
        Rebuild the spatial grid with current entity positions (legacy method).
        Kept for compatibility but no longer used in update loop.
        """
        from app.simulation.models.entity import Entity

        self.spatial_grid.clear()

        # Insert all entities into grid
        entities = self.get_objects_by_type(Entity)
        for entity in entities:
            self.spatial_grid.insert(entity.id, entity.position)
            entity._last_grid_cell = self.spatial_grid._get_cell_coords(entity.position)

    def query_nearby_entities(self, position: Vector2D, radius: float,
                              exclude_id: Optional[str] = None) -> List['GameObject']:
        """
        Query entities within a radius of a position using the spatial grid.

        Args:
            position: Center position to query around
            radius: Search radius
            exclude_id: Optional entity ID to exclude from results

        Returns:
            List of GameObject instances within the radius
        """
        entity_ids = self.spatial_grid.query_radius(position, radius, exclude_id)
        return [self._objects[eid] for eid in entity_ids if eid in self._objects]

    def get_grid_stats(self) -> Dict:
        """Get spatial grid statistics for debugging."""
        return self.spatial_grid.get_stats()

    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities from the simulation and update species populations."""
        from app.simulation.models.entity import Entity, EntityState
        from app.simulation.models.species import Species

        entities = self.get_objects_by_type(Entity)
        dead_entities = [e for e in entities if e.state == EntityState.DEAD]

        if not dead_entities:
            return

        # Get all species for population tracking
        species_dict = {s.id: s for s in self.get_objects_by_type(Species)}

        for entity in dead_entities:
            # Update species population count
            if entity.species_id in species_dict:
                species = species_dict[entity.species_id]
                species.population = max(0, species.population - 1)

            # Remove from context
            self.unregister(entity)

        logging.debug(f"Cleaned up {len(dead_entities)} dead entities")