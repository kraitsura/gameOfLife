"""
Spatial Grid for efficient neighbor queries in the simulation.

Uses a 2D spatial hash grid to partition the world into cells, enabling
O(1) average-case neighbor queries instead of O(n²) brute force searches.
"""

from typing import Dict, Set, List, Tuple, Optional
from app.simulation.core.vector import Vector2D
import math


class SpatialGrid:
    """
    2D spatial hash grid for efficient entity neighbor queries.

    The grid divides the world into uniform cells. Each cell maintains a set
    of entity IDs that currently occupy it. This enables fast queries like:
    - "What entities are near position (x, y)?"
    - "What entities are in this rectangular region?"
    - "What are the neighbors of entity X?"

    The grid is rebuilt each frame by clearing and re-inserting all entities.
    """

    def __init__(self, world_width: int, world_height: int, cell_size: float):
        """
        Initialize the spatial grid.

        Args:
            world_width: Width of the world in simulation units
            world_height: Height of the world in simulation units
            cell_size: Size of each grid cell (should match typical interaction distance)
        """
        self.world_width = world_width
        self.world_height = world_height
        self.cell_size = cell_size

        # Calculate grid dimensions
        self.cols = math.ceil(world_width / cell_size)
        self.rows = math.ceil(world_height / cell_size)

        # HashMap: (col, row) -> Set of entity IDs in that cell
        self._cells: Dict[Tuple[int, int], Set[str]] = {}

        # Reverse lookup: entity_id -> (col, row) for fast removal
        self._entity_cells: Dict[str, Tuple[int, int]] = {}

    def clear(self) -> None:
        """Clear all entities from the grid."""
        self._cells.clear()
        self._entity_cells.clear()

    def _get_cell_coords(self, position: Vector2D) -> Tuple[int, int]:
        """
        Convert world position to grid cell coordinates.

        Args:
            position: World position

        Returns:
            (col, row) tuple of grid cell coordinates
        """
        col = int(position.x / self.cell_size)
        row = int(position.y / self.cell_size)

        # Clamp to grid bounds
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))

        return (col, row)

    def insert(self, entity_id: str, position: Vector2D) -> None:
        """
        Insert an entity into the grid at the given position.

        Args:
            entity_id: Unique identifier for the entity
            position: World position of the entity
        """
        cell_coords = self._get_cell_coords(position)

        # Add to cell
        if cell_coords not in self._cells:
            self._cells[cell_coords] = set()
        self._cells[cell_coords].add(entity_id)

        # Track entity's cell for fast removal
        self._entity_cells[entity_id] = cell_coords

    def remove(self, entity_id: str) -> None:
        """
        Remove an entity from the grid.

        Args:
            entity_id: Unique identifier for the entity
        """
        if entity_id not in self._entity_cells:
            return

        cell_coords = self._entity_cells[entity_id]

        if cell_coords in self._cells:
            self._cells[cell_coords].discard(entity_id)

            # Clean up empty cells
            if not self._cells[cell_coords]:
                del self._cells[cell_coords]

        del self._entity_cells[entity_id]

    def query_radius(self, position: Vector2D, radius: float, exclude_id: Optional[str] = None) -> List[str]:
        """
        Query all entities within a circular radius of a position.

        Args:
            position: Center position to query around
            radius: Radius of the circular query region
            exclude_id: Optional entity ID to exclude from results (e.g., the querying entity)

        Returns:
            List of entity IDs within the radius
        """
        # Calculate bounding box of cells to check
        min_col = max(0, int((position.x - radius) / self.cell_size))
        max_col = min(self.cols - 1, int((position.x + radius) / self.cell_size))
        min_row = max(0, int((position.y - radius) / self.cell_size))
        max_row = min(self.rows - 1, int((position.y + radius) / self.cell_size))

        results = []

        # Check all cells in the bounding box
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                cell_coords = (col, row)
                if cell_coords in self._cells:
                    for entity_id in self._cells[cell_coords]:
                        if exclude_id and entity_id == exclude_id:
                            continue
                        results.append(entity_id)

        return results

    def query_rect(self, min_x: float, min_y: float, max_x: float, max_y: float,
                   exclude_id: Optional[str] = None) -> List[str]:
        """
        Query all entities within a rectangular region.

        Args:
            min_x: Minimum x coordinate
            min_y: Minimum y coordinate
            max_x: Maximum x coordinate
            max_y: Maximum y coordinate
            exclude_id: Optional entity ID to exclude from results

        Returns:
            List of entity IDs within the rectangle
        """
        # Calculate cell range
        min_col = max(0, int(min_x / self.cell_size))
        max_col = min(self.cols - 1, int(max_x / self.cell_size))
        min_row = max(0, int(min_y / self.cell_size))
        max_row = min(self.rows - 1, int(max_y / self.cell_size))

        results = []

        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                cell_coords = (col, row)
                if cell_coords in self._cells:
                    for entity_id in self._cells[cell_coords]:
                        if exclude_id and entity_id == exclude_id:
                            continue
                        results.append(entity_id)

        return results

    def get_neighbors(self, position: Vector2D, exclude_id: Optional[str] = None) -> List[str]:
        """
        Get all entities in the same cell and adjacent cells (3x3 neighborhood).

        Args:
            position: Position to query around
            exclude_id: Optional entity ID to exclude from results

        Returns:
            List of entity IDs in neighboring cells
        """
        center_col, center_row = self._get_cell_coords(position)

        results = []

        # Check 3x3 grid of cells
        for col in range(max(0, center_col - 1), min(self.cols, center_col + 2)):
            for row in range(max(0, center_row - 1), min(self.rows, center_row + 2)):
                cell_coords = (col, row)
                if cell_coords in self._cells:
                    for entity_id in self._cells[cell_coords]:
                        if exclude_id and entity_id == exclude_id:
                            continue
                        results.append(entity_id)

        return results

    def get_cell_at_position(self, position: Vector2D) -> Set[str]:
        """
        Get all entity IDs in the cell containing the given position.

        Args:
            position: World position

        Returns:
            Set of entity IDs in that cell (empty set if cell is empty)
        """
        cell_coords = self._get_cell_coords(position)
        return self._cells.get(cell_coords, set()).copy()

    def get_stats(self) -> Dict:
        """
        Get statistics about the grid for debugging/monitoring.

        Returns:
            Dictionary with grid statistics
        """
        total_entities = len(self._entity_cells)
        occupied_cells = len(self._cells)
        total_cells = self.cols * self.rows

        # Calculate average and max entities per cell
        entities_per_cell = [len(entities) for entities in self._cells.values()]
        avg_entities = sum(entities_per_cell) / len(entities_per_cell) if entities_per_cell else 0
        max_entities = max(entities_per_cell) if entities_per_cell else 0

        return {
            "total_entities": total_entities,
            "occupied_cells": occupied_cells,
            "total_cells": total_cells,
            "occupancy_rate": occupied_cells / total_cells if total_cells > 0 else 0,
            "avg_entities_per_cell": avg_entities,
            "max_entities_per_cell": max_entities,
            "cell_size": self.cell_size,
            "grid_dimensions": (self.cols, self.rows)
        }
