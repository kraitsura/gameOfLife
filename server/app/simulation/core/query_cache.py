"""
Frame-level query cache for spatial queries (Phase 2 optimization).

Caches spatial query results for the duration of a single frame,
eliminating redundant queries when multiple components query the
same radius around the same entity.
"""

from typing import Dict, List, Tuple, Optional, Callable, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext
    from app.simulation.models.entity import Entity

class FrameQueryCache:
    """
    Frame-level cache for spatial queries.

    Caches results of query_nearby_entities() calls within a single frame.
    When multiple components (physics, diet, social) query the same entity
    with the same radius, the cached result is returned instead of
    performing another spatial grid lookup.

    The cache is invalidated at the start of each frame to ensure
    fresh position data.
    """

    def __init__(self):
        # Cache key: (entity_id, radius, frame_id) -> List of entities
        self._cache: Dict[Tuple[str, float, int], List['Entity']] = {}
        self._frame_id: int = 0

        # Statistics for monitoring
        self._query_stats: Dict[str, int] = defaultdict(int)

    def get_nearby(
        self,
        entity_id: str,
        radius: float,
        context: 'SimulationContext',
        entity_filter: Optional[Callable[['Entity'], bool]] = None
    ) -> List['Entity']:
        """
        Get nearby entities with caching.

        If a result exists for this (entity_id, radius, frame_id) combination,
        returns the cached result. Otherwise, performs the query and caches it.

        Args:
            entity_id: ID of the entity querying
            radius: Search radius
            context: Simulation context for performing queries
            entity_filter: Optional filter function to apply to results

        Returns:
            List of nearby entities within radius
        """
        from app.simulation.models.entity import Entity

        # Create cache key (without filter in key - filter is applied after caching)
        cache_key = (entity_id, radius, self._frame_id)

        if cache_key in self._cache:
            self._query_stats['cache_hits'] += 1
            results = self._cache[cache_key]
        else:
            # Cache miss - perform actual query
            self._query_stats['cache_misses'] += 1

            entity = context.get_by_id(Entity, entity_id)
            if not entity:
                return []

            results = context.query_nearby_entities(
                entity.position,
                radius,
                exclude_id=entity_id
            )

            # Cache the unfiltered results
            self._cache[cache_key] = results

        # Apply filter if provided (after caching)
        if entity_filter:
            return [e for e in results if entity_filter(e)]

        return results

    def get_nearby_multi_radius(
        self,
        entity_id: str,
        radii: List[float],
        context: 'SimulationContext'
    ) -> Dict[float, List['Entity']]:
        """
        Perform queries for multiple radii in one optimized call.

        Queries the largest radius once, then partitions results into
        radius buckets. More efficient than multiple separate queries.

        Args:
            entity_id: ID of the entity querying
            radii: List of search radii
            context: Simulation context

        Returns:
            Dictionary mapping radius -> list of entities within that radius
        """
        from app.simulation.models.entity import Entity

        if not radii:
            return {}

        # Sort radii ascending
        sorted_radii = sorted(radii)

        # Query largest radius (gets all entities we need)
        all_entities = self.get_nearby(entity_id, sorted_radii[-1], context)

        # Get entity position for distance calculations
        entity = context.get_by_id(Entity, entity_id)
        if not entity:
            return {r: [] for r in radii}

        # Partition into radius buckets
        results = {r: [] for r in radii}

        for other in all_entities:
            dist = (entity.position - other.position).magnitude()
            for r in sorted_radii:
                if dist <= r:
                    results[r].append(other)

        return results

    def new_frame(self) -> None:
        """
        Clear cache for new frame.

        Called at the start of each simulation update to ensure
        queries use fresh position data.
        """
        self._cache.clear()
        self._frame_id += 1

    def get_stats(self) -> dict:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with hit rate and query counts
        """
        total = self._query_stats['cache_hits'] + self._query_stats['cache_misses']
        hit_rate = self._query_stats['cache_hits'] / total if total > 0 else 0

        return {
            'hits': self._query_stats['cache_hits'],
            'misses': self._query_stats['cache_misses'],
            'total_queries': total,
            'hit_rate': hit_rate,
            'frame': self._frame_id,
            'cache_size': len(self._cache)
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._query_stats.clear()
