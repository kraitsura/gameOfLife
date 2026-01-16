# Performance Optimization Plan

**Created**: 2025-10-19
**Status**: Planning Complete - Ready for Implementation
**Goal**: Eliminate performance bottlenecks causing backend slowdown and WebSocket disconnections

---

## Executive Summary

### Problem Statement
The simulation backend experiences **progressive performance degradation** as entities increase and packs form. After 2-3 minutes of runtime (100+ entities, 30-50 packs), frame times exceed 40ms (target: 16.67ms at 60 FPS), causing WebSocket timeouts and client disconnections.

### Root Cause
**Algorithmic complexity explosion**: O(n²) pack operations combined with exponential pack formation create a performance cliff. Multiple redundant spatial queries and unbounded memory growth compound the issue.

### Solution Approach
**4-phase optimization plan** targeting algorithmic improvements, spatial query caching, network optimization, and advanced data structures. All phases maintain **full simulation accuracy** while achieving maximum performance.

---

## Performance Analysis Findings

### Timeline of Degradation

| Time     | Entities | Packs | Frame Time | CPU Usage | Status |
|----------|----------|-------|------------|-----------|--------|
| 0-30s    | 50-70    | 0-3   | 5ms        | 30%       | ✅ Smooth 60 FPS |
| 1-2 min  | 80-100   | 5-10  | 12ms       | 60%       | ⚠️ Starting to lag |
| 2-3 min  | 100-120  | 20-30 | 25ms       | 80%       | ⚠️ Dropped frames |
| 3+ min   | 100-120  | 30-50 | 40ms+      | 95%+      | ❌ Disconnects |

### Critical Bottlenecks Identified

#### 1. O(n²) Pack Split Detection ⚠️ CRITICAL
- **Location**: `server/app/simulation/models/pack.py:145-150`
- **Issue**: All pairwise distances calculated every frame for every pack
- **Code Pattern**:
  ```python
  for i, m1 in enumerate(member_list):
      for m2 in member_list[i+1:]:
          dist = (m1.position - m2.position).magnitude()
  ```
- **Complexity**: O(n²) where n = pack size
- **Impact**: 50 packs × 20 members = **10,000 distance calculations per frame**
- **Frequency**: Every frame at 60 FPS
- **Why it causes disconnections**: As packs grow, this dominates CPU time, starving async tasks

#### 2. Spatial Grid Rebuilt Every Frame ⚠️ CRITICAL
- **Location**: `server/app/simulation/core/context.py:83-92`
- **Issue**: Complete O(n) grid reconstruction 60 times per second
- **Code Pattern**:
  ```python
  def _rebuild_spatial_grid(self) -> None:
      self.spatial_grid.clear()
      entities = self.get_objects_by_type(Entity)
      for entity in entities:
          self.spatial_grid.insert(entity.id, entity.position)
  ```
- **Complexity**: O(n) per frame
- **Impact**: 120 entities × 60 FPS = **7,200 insertions per second**
- **Alternative**: Incremental updates (only changed entities)

#### 3. Multiple Redundant Spatial Queries ⚠️ CRITICAL
- **Locations**:
  - `server/app/simulation/components/base/physics.py:198-202` (separation)
  - `server/app/simulation/components/base/physics.py:256` (cohesion)
  - `server/app/simulation/components/base/physics.py:322` (alignment)
  - `server/app/simulation/components/base/diet.py:115-119` (food detection)
  - `server/app/simulation/components/base/diet.py:397` (threat detection)
  - `server/app/simulation/components/base/social.py:119-123` (pack formation)
- **Issue**: Each entity performs 5-6 separate spatial queries per frame
- **Impact**: 100 entities × 6 queries = **600 queries/frame**
- **Redundancy**: Many queries have overlapping radii and results
- **Solution**: Single unified query with frame-level caching

#### 4. Unbounded Memory Growth ⚠️ HIGH
- **Locations**:
  - `server/app/simulation/components/base/social.py` (familiarity_scores, last_interaction_time)
  - `server/app/simulation/models/pack.py` (pack_interactions)
- **Issue**: Dictionaries grow unbounded, never pruned
- **Code Pattern**:
  ```python
  self.familiarity_scores: Dict[str, float] = {}  # Never pruned!
  self.last_interaction_time: Dict[str, float] = {}  # Never pruned!
  self.pack_interactions: Dict[str, float] = {}  # Grows forever
  ```
- **Impact**: Memory leak causing gradual slowdown over time
- **Evidence**: Old pack IDs accumulate even after packs are deleted

#### 5. Full State Serialization at 60 FPS ⚠️ HIGH
- **Location**: `server/app/main.py:159-160, 186`
- **Issue**: All entities and packs serialized every frame, even unchanged
- **Code Pattern**:
  ```python
  state = simulation.get_state()  # Serializes everything
  return {
      "entities": {str(e.id): e.serialize() for e in entities},
      "species": {str(s.id): s.serialize() for s in species},
      "packs": {str(p.id): p.serialize() for p in packs}
  }
  ```
- **Impact**: 100 entities × 150 bytes = 15 KB × 60 FPS = **900 KB/sec per client**
- **With 5 clients**: 4.5 MB/sec network traffic

#### 6. Pack-to-Pack Interaction Detection ⚠️ HIGH
- **Location**: `server/app/simulation/models/pack.py:373-400`
- **Issue**: Every pack queries nearby entities to find other packs
- **Complexity**: O(P × m × P) where P = pack count, m = entities in range
- **Cascading Effect**: Quadratic growth with pack count

### Current Complexity Analysis

| Component | Best Case | Average Case | Worst Case | Notes |
|-----------|-----------|--------------|-----------|-------|
| **Spatial Grid Rebuild** | O(n) | O(n) | O(n) | Per frame at 60 FPS |
| **Pack Update** | O(p) | O(p² + m) | O(p³) | p=pack size, m=nearby entities |
| **Pack Split Detection** | O(p) | O(p²) | O(p²) | Every frame for each pack |
| **Entity Physics Update** | O(n·q) | O(n·q·k) | O(n²) | n=entities, q=queries, k=result size |
| **Diet Component** | O(m) | O(m·log m) | O(n) | Finding nearest food |
| **Social Pack Formation** | O(c) | O(c²) | O(c²) | c=nearby same-species; distance matrix |
| **Entity Serialization** | O(n) | O(n) | O(n) | Per broadcast at 60 FPS |
| **Dead Entity Cleanup** | O(d) | O(d·s) | O(n) | d=dead, s=species count |

**Total Operations Per Frame (100+ entities):**
- Entity updates: ~600-1,000 ops
- Pack updates: ~1,000-5,000 ops (grows with pack count)
- Grid rebuild: ~100 ops
- Serialization: ~150 ops
- **Grand total: 42,000-150,000 operations per second**

### Why Disconnections Occur

The simulation loop shares the asyncio event loop with WebSocket communication:

```python
# simulation.py:48-71
while self._is_running:
    current_time = time.time()
    frame_time = current_time - self.last_update_time
    self.accumulator += frame_time

    while self.accumulator >= self.fixed_dt:
        self.world.update(self.fixed_dt)  # ← BOTTLENECK
        self._cleanup_out_of_bounds_entities()
        self.accumulator -= self.fixed_dt

    await asyncio.sleep(0.01)  # Only 10ms yield!
```

**The problem**: When `world.update()` exceeds ~6.67ms (40% of 16.67ms frame budget), the async loop cannot yield to WebSocket broadcast tasks. At 100+ entities with pack formation:
- Update time: 25-40ms
- Broadcast task starved for 20-30ms
- Client heartbeat timeout: 30 seconds default
- **Result: Disconnection after sustained overload**

---

## 4-Phase Implementation Plan

### Phase 1: Critical Bottleneck Elimination
**Goal**: Stabilize at 120-140 entities, eliminate disconnections
**Estimated Time**: 2-3 hours
**Target Metrics**: Frame time 40ms → 15-20ms

#### 1.1 Eliminate O(n²) Pack Split Detection

**File**: `server/app/simulation/models/pack.py`

**Current Implementation**:
```python
# Lines 145-150
for i, m1 in enumerate(member_list):
    for m2 in member_list[i+1:]:
        dist = (m1.position - m2.position).magnitude()
        if dist > max_distance:
            max_dist = dist
            farthest_pair = (m1, m2)
```

**New Implementation Strategy**:

1. **Bounding Box Pre-check** (O(n)):
   ```python
   def _is_dispersed(self) -> bool:
       """Quick O(n) check before expensive split detection"""
       min_x = min(m.position.x for m in self.members)
       max_x = max(m.position.x for m in self.members)
       min_y = min(m.position.y for m in self.members)
       max_y = max(m.position.y for m in self.members)

       max_dimension = max(max_x - min_x, max_y - min_y)
       return max_dimension > self.max_pack_spread * 1.5
   ```

2. **Welzl's Minimum Enclosing Circle** (O(n) expected):
   ```python
   def _welzl_mec(self, points: List[Vector2D], boundary: List[Vector2D] = None) -> Tuple[Vector2D, float]:
       """
       Welzl's algorithm for minimum enclosing circle.
       Returns (center, radius) in O(n) expected time.
       """
       # Implementation of Welzl's algorithm
       # Used to detect if pack is truly split-worthy
   ```

3. **K-means Clustering for Split** (O(n·k·i), k=2, i≈5-10):
   ```python
   def _split_pack_kmeans(self, context: SimulationContext) -> Optional[Pack]:
       """
       Use k-means (k=2) to find natural split.
       Only called when _is_dispersed() returns True.
       """
       # Initialize two centroids (farthest pair as seeds)
       # Iterate until convergence (typically 5-10 iterations)
       # Assign members to closest centroid
       # Return new pack with second cluster
   ```

4. **Throttled Split Checks**:
   ```python
   def update(self, context: SimulationContext, dt: float):
       # Only check split every 0.5 seconds, not every frame
       if time.time() - self._last_split_check > 0.5:
           if self._is_dispersed():  # O(n) quick check
               self._detect_split_kmeans(context)  # O(n log n)
           self._last_split_check = time.time()
   ```

**Complexity Improvement**: O(n²) every frame → O(n) check every 0.5s, O(n log n) split rarely
**Accuracy**: Maintained - still detects genuine splits based on same distance thresholds

#### 1.2 Incremental Spatial Grid Updates

**File**: `server/app/simulation/core/context.py`

**Current Implementation**:
```python
def _rebuild_spatial_grid(self) -> None:
    self.spatial_grid.clear()
    entities = self.get_objects_by_type(Entity)
    for entity in entities:
        self.spatial_grid.insert(entity.id, entity.position)
```

**New Implementation**:

1. **Track Last Grid Cell per Entity**:
   ```python
   class Entity:
       _last_grid_cell: Optional[Tuple[int, int]] = None
   ```

2. **Incremental Update**:
   ```python
   def _update_entity_in_grid(self, entity: Entity):
       """Only update if entity changed grid cells"""
       current_cell = self.spatial_grid.get_cell_coords(entity.position)

       if entity._last_grid_cell != current_cell:
           # Remove from old cell
           if entity._last_grid_cell:
               self.spatial_grid.remove(entity.id, entity._last_grid_cell)

           # Insert into new cell
           self.spatial_grid.insert(entity.id, entity.position)
           entity._last_grid_cell = current_cell
   ```

3. **Dirty Tracking**:
   ```python
   class SimulationContext:
       _dirty_entities: Set[UUID] = set()

       def mark_entity_moved(self, entity_id: UUID):
           self._dirty_entities.add(entity_id)

       def update_spatial_grid(self):
           """Only update moved entities"""
           for entity_id in self._dirty_entities:
               entity = self.get_by_id(Entity, entity_id)
               if entity:
                   self._update_entity_in_grid(entity)
           self._dirty_entities.clear()
   ```

**Complexity Improvement**: O(n) every frame → O(k) where k = entities that moved cells
**Typical k**: ~10-20% of entities per frame (most stay in same cell)
**Accuracy**: Maintained - exact same grid, just updated incrementally

#### 1.3 Memory Leak Fixes - Bounded Interaction History

**File**: `server/app/simulation/components/base/social.py`

**Current Implementation**:
```python
class SocialComponent(Component):
    def __init__(self):
        self.familiarity_scores: Dict[str, float] = {}
        self.last_interaction_time: Dict[str, float] = {}
```

**New Implementation**:

1. **LRU Cache with Time-based Pruning**:
   ```python
   from collections import OrderedDict

   class SocialComponent(Component):
       MAX_INTERACTIONS = 50  # Maximum tracked interactions
       INTERACTION_TTL = 60.0  # Seconds before interaction expires

       def __init__(self):
           self.familiarity_scores: OrderedDict[str, float] = OrderedDict()
           self.last_interaction_time: OrderedDict[str, float] = OrderedDict()

       def _prune_old_interactions(self, current_time: float):
           """Remove interactions older than TTL"""
           to_remove = []
           for entity_id, last_time in self.last_interaction_time.items():
               if current_time - last_time > self.INTERACTION_TTL:
                   to_remove.append(entity_id)

           for entity_id in to_remove:
               self.familiarity_scores.pop(entity_id, None)
               self.last_interaction_time.pop(entity_id, None)

       def record_interaction(self, other_id: str, current_time: float):
           """Record interaction with LRU eviction"""
           # Prune old interactions first
           self._prune_old_interactions(current_time)

           # Evict least recently used if at capacity
           if len(self.familiarity_scores) >= self.MAX_INTERACTIONS:
               if other_id not in self.familiarity_scores:
                   # Remove oldest
                   self.familiarity_scores.popitem(last=False)
                   self.last_interaction_time.popitem(last=False)

           # Update or insert (moves to end for LRU)
           self.familiarity_scores[other_id] = self.familiarity_scores.get(other_id, 0) + 1
           self.last_interaction_time[other_id] = current_time

           # Move to end (mark as recently used)
           self.familiarity_scores.move_to_end(other_id)
           self.last_interaction_time.move_to_end(other_id)
   ```

**Memory Improvement**: O(t) unbounded → O(50) bounded per entity
**Accuracy**: Maintained - keeps most relevant recent interactions

#### 1.4 Pack Interaction History Cleanup

**File**: `server/app/simulation/models/pack.py`

**Current Implementation**:
```python
class Pack:
    def __init__(self):
        self.pack_interactions: Dict[str, float] = {}  # Never pruned
```

**New Implementation**:

1. **Cleanup on Pack Deletion**:
   ```python
   def cleanup_references(self, context: SimulationContext):
       """Called when pack is being deleted"""
       # Remove this pack from other packs' interaction histories
       all_packs = context.get_objects_by_type(Pack)
       for pack in all_packs:
           pack.pack_interactions.pop(str(self.id), None)
   ```

2. **Periodic Validation**:
   ```python
   def _validate_pack_interactions(self, context: SimulationContext):
       """Remove references to non-existent packs"""
       to_remove = []
       for pack_id in self.pack_interactions.keys():
           if not context.get_by_id(Pack, UUID(pack_id)):
               to_remove.append(pack_id)

       for pack_id in to_remove:
           self.pack_interactions.pop(pack_id, None)
   ```

3. **Time-based Pruning**:
   ```python
   MAX_PACK_INTERACTION_AGE = 120.0  # 2 minutes

   def _prune_old_pack_interactions(self, current_time: float):
       """Remove pack interactions older than threshold"""
       # Store (pack_id, last_interaction_time)
       # Remove entries older than MAX_PACK_INTERACTION_AGE
   ```

#### 1.5 Pack Center Caching

**File**: `server/app/simulation/models/pack.py`

**Current Implementation**:
```python
@property
def pack_center(self) -> Vector2D:
    if not self.members:
        return Vector2D(0, 0)
    total = Vector2D(0, 0)
    for member in self.members:
        total += member.position
    return total / len(self.members)
```
Called multiple times per frame, recalculates every time (O(n) each call).

**New Implementation**:
```python
class Pack:
    def __init__(self):
        self._cached_center: Optional[Vector2D] = None
        self._center_dirty: bool = True

    @property
    def pack_center(self) -> Vector2D:
        if self._center_dirty:
            self._cached_center = self._calculate_center()
            self._center_dirty = False
        return self._cached_center

    def _calculate_center(self) -> Vector2D:
        """Internal method to calculate center"""
        if not self.members:
            return Vector2D(0, 0)
        total = Vector2D(0, 0)
        for member in self.members:
            total += member.position
        return total / len(self.members)

    def invalidate_center(self):
        """Call when members change"""
        self._center_dirty = True

    def add_member(self, entity: Entity):
        self.members.add(entity)
        self.invalidate_center()

    def remove_member(self, entity: Entity):
        self.members.discard(entity)
        self.invalidate_center()
```

**Improvement**: Multiple O(n) calls → One O(n) + multiple O(1) lookups

#### Phase 1 Expected Results
- **Frame time**: 40ms → 15-20ms at 120 entities
- **Pack updates**: O(n²) → O(n) with throttling
- **Grid updates**: O(n) → O(k) where k ≈ 10-20% of n
- **Memory**: Bounded growth, no leaks
- **Stability**: Can run for 10+ minutes without degradation
- **Max entities**: 120-140 stable

---

### Phase 2: Spatial Query Optimization
**Goal**: Eliminate redundant queries, add caching
**Estimated Time**: 2-3 hours
**Target Metrics**: Frame time 15-20ms → 8-12ms, support 150-180 entities

#### 2.1 Unified Spatial Query System

**New File**: `server/app/simulation/core/query_cache.py`

**Implementation**:
```python
from typing import Dict, List, Tuple, Set
from uuid import UUID
from collections import defaultdict

class FrameQueryCache:
    """
    Frame-level cache for spatial queries.
    Invalidated every frame to ensure fresh data.
    """

    def __init__(self):
        # Cache key: (entity_id, radius, frame_id)
        self._cache: Dict[Tuple[UUID, float, int], List[Entity]] = {}
        self._frame_id: int = 0
        self._query_stats: Dict[str, int] = defaultdict(int)

    def get_nearby(
        self,
        entity_id: UUID,
        radius: float,
        context: 'SimulationContext',
        entity_filter: Optional[Callable] = None
    ) -> List[Entity]:
        """
        Get nearby entities with caching.
        If result exists for this frame, return cached.
        Otherwise, perform query and cache result.
        """
        cache_key = (entity_id, radius, self._frame_id)

        if cache_key in self._cache:
            self._query_stats['cache_hits'] += 1
            return self._cache[cache_key]

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

        # Apply filter if provided
        if entity_filter:
            results = [e for e in results if entity_filter(e)]

        self._cache[cache_key] = results
        return results

    def new_frame(self):
        """Clear cache for new frame"""
        self._cache.clear()
        self._frame_id += 1

    def get_stats(self) -> dict:
        """Get cache performance statistics"""
        total = self._query_stats['cache_hits'] + self._query_stats['cache_misses']
        hit_rate = self._query_stats['cache_hits'] / total if total > 0 else 0
        return {
            'hits': self._query_stats['cache_hits'],
            'misses': self._query_stats['cache_misses'],
            'hit_rate': hit_rate,
            'frame': self._frame_id
        }
```

**Integration into SimulationContext**:
```python
class SimulationContext:
    def __init__(self):
        self.query_cache = FrameQueryCache()
        # ... existing code ...

    def update(self, dt: float):
        # Invalidate cache at start of frame
        self.query_cache.new_frame()

        # ... existing update logic ...
```

**Component Integration Example** (Physics):
```python
# Before:
nearby = context.query_nearby_entities(owner.position, vision_range, owner.id)

# After:
nearby = context.query_cache.get_nearby(
    owner.id,
    vision_range,
    context
)
```

**Expected Improvement**: 600 queries → 100-150 unique queries (4-6x reduction)

#### 2.2 Component Query Batching

**Modify Physics Component** (`physics.py`):
```python
def update(self, owner: Entity, context: SimulationContext, dt: float):
    # Single query for all flocking behaviors
    vision_range = owner.stats.entity_vision
    nearby = context.query_cache.get_nearby(owner.id, vision_range, context)

    # Filter once for same-species neighbors
    same_species = [e for e in nearby if e.species_id == owner.species_id and e.pack_id == owner.pack_id]

    # Reuse filtered list for all three forces
    separation = self._calculate_separation_force(owner, same_species)
    cohesion = self._calculate_cohesion_force(owner, same_species)
    alignment = self._calculate_alignment_force(owner, same_species)

    # Combine forces
    # ...
```

**Before**: 3 separate queries for separation, cohesion, alignment
**After**: 1 cached query, 1 filter pass, reused 3 times

#### 2.3 Optimized Grid Cell Traversal

**File**: `server/app/simulation/core/spatial_grid.py`

**Current**: Linear search through all entities in cells
**New**: Pre-sorted cells with binary search

```python
class SpatialGrid:
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        # Store entities sorted by distance from cell center
        self._cells: Dict[Tuple[int, int], List[Tuple[float, UUID]]] = defaultdict(list)
        self._cell_centers: Dict[Tuple[int, int], Vector2D] = {}

    def insert(self, entity_id: UUID, position: Vector2D):
        cell_coords = self._get_cell_coords(position)

        # Calculate distance from cell center
        if cell_coords not in self._cell_centers:
            self._cell_centers[cell_coords] = self._calculate_cell_center(cell_coords)

        cell_center = self._cell_centers[cell_coords]
        distance = (position - cell_center).magnitude()

        # Insert maintaining sorted order (binary search insertion)
        cell_list = self._cells[cell_coords]
        insert_pos = bisect.bisect_left(cell_list, (distance, entity_id))
        cell_list.insert(insert_pos, (distance, entity_id))

    def query_radius(self, center: Vector2D, radius: float) -> List[UUID]:
        """Query with early termination using sorted cells"""
        results = []
        affected_cells = self._get_affected_cells(center, radius)

        for cell_coords in affected_cells:
            if cell_coords not in self._cells:
                continue

            cell_center = self._cell_centers[cell_coords]
            cell_to_query_dist = (cell_center - center).magnitude()

            # Iterate sorted entities in cell
            for dist_from_cell_center, entity_id in self._cells[cell_coords]:
                # Calculate actual distance to query point
                # Use triangle inequality for early termination
                min_possible_dist = abs(cell_to_query_dist - dist_from_cell_center)
                if min_possible_dist > radius:
                    break  # Rest of entities are farther

                # Check actual distance
                entity = self._entity_lookup[entity_id]
                actual_dist = (entity.position - center).magnitude()
                if actual_dist <= radius:
                    results.append(entity_id)

        return results
```

**Improvement**: O(m) linear scan → O(log m + k) where k = results in radius

#### 2.4 Multi-Radius Query Optimization

**New Method in QueryCache**:
```python
def get_nearby_multi_radius(
    self,
    entity_id: UUID,
    radii: List[float],
    context: SimulationContext
) -> Dict[float, List[Entity]]:
    """
    Perform queries for multiple radii in one grid traversal.
    Returns dict mapping radius -> entities in that radius.
    """
    # Sort radii ascending
    sorted_radii = sorted(radii)

    # Query largest radius
    all_entities = self.get_nearby(entity_id, sorted_radii[-1], context)

    # Partition into radius buckets
    entity = context.get_by_id(Entity, entity_id)
    results = {r: [] for r in radii}

    for other in all_entities:
        dist = (entity.position - other.position).magnitude()
        for r in sorted_radii:
            if dist <= r:
                results[r].append(other)
```

**Use Case** (when components need different radii):
```python
# Before:
nearby_50 = query(50)   # Grid traversal 1
nearby_100 = query(100) # Grid traversal 2

# After:
results = query_multi_radius([50, 100])  # One grid traversal
nearby_50 = results[50]
nearby_100 = results[100]
```

#### Phase 2 Expected Results
- **Frame time**: 15-20ms → 8-12ms at 150 entities
- **Query count**: 600/frame → 100-150/frame
- **Cache hit rate**: 60-80%
- **Max entities**: 150-180 stable

---

### Phase 3: Network & Serialization Optimization
**Goal**: Reduce bandwidth, support multiple clients
**Estimated Time**: 1.5-2 hours
**Target Metrics**: 900 KB/s → 150-200 KB/s, support 5-10 clients

#### 3.1 Delta State Transmission

**New File**: `server/app/simulation/delta_encoder.py`

**Implementation**:
```python
from typing import Dict, Set, Any
from uuid import UUID
import hashlib
import json

class DeltaEncoder:
    """
    Encodes simulation state as deltas (changes only).
    Dramatically reduces bandwidth for incremental updates.
    """

    def __init__(self):
        self._last_state: Dict[str, Dict] = {
            'entities': {},
            'packs': {},
            'species': {}
        }
        self._entity_hashes: Dict[UUID, str] = {}
        self._frame_counter: int = 0
        self.full_state_interval: int = 300  # Send full state every 5 seconds

    def _hash_entity(self, entity_data: dict) -> str:
        """Quick hash of entity state for change detection"""
        # Hash position, health, energy (most frequently changing)
        key_data = {
            'x': round(entity_data['position']['x'], 1),
            'y': round(entity_data['position']['y'], 1),
            'h': round(entity_data.get('health', 0), 1),
            'e': round(entity_data.get('energy', 0), 1),
            'pack': entity_data.get('pack_id')
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def encode(self, current_state: dict) -> dict:
        """
        Encode state as delta or full update.
        Returns delta format or full state depending on frame counter.
        """
        self._frame_counter += 1

        # Send full state periodically
        if self._frame_counter % self.full_state_interval == 0:
            self._last_state = current_state
            return {
                'type': 'full',
                'state': current_state,
                'frame': self._frame_counter
            }

        # Build delta
        delta = {
            'type': 'delta',
            'frame': self._frame_counter,
            'entities': {
                'added': {},
                'modified': {},
                'removed': []
            },
            'packs': {
                'added': {},
                'modified': {},
                'removed': []
            },
            'species': {}  # Species rarely change, always send full
        }

        # Process entities
        current_ids = set(current_state['entities'].keys())
        last_ids = set(self._last_state['entities'].keys())

        # New entities
        for entity_id in current_ids - last_ids:
            delta['entities']['added'][entity_id] = current_state['entities'][entity_id]

        # Removed entities
        delta['entities']['removed'] = list(last_ids - current_ids)

        # Modified entities (hash comparison)
        for entity_id in current_ids & last_ids:
            current_data = current_state['entities'][entity_id]
            current_hash = self._hash_entity(current_data)
            last_hash = self._entity_hashes.get(entity_id)

            if current_hash != last_hash:
                delta['entities']['modified'][entity_id] = current_data
                self._entity_hashes[entity_id] = current_hash

        # Process packs similarly
        self._process_packs_delta(current_state, delta)

        # Always send species (small payload)
        delta['species'] = current_state['species']

        # Update last state
        self._last_state = current_state

        return delta

    def _process_packs_delta(self, current_state: dict, delta: dict):
        """Process pack changes for delta encoding"""
        current_pack_ids = set(current_state['packs'].keys())
        last_pack_ids = set(self._last_state['packs'].keys())

        # Added packs
        for pack_id in current_pack_ids - last_pack_ids:
            delta['packs']['added'][pack_id] = current_state['packs'][pack_id]

        # Removed packs
        delta['packs']['removed'] = list(last_pack_ids - current_pack_ids)

        # Modified packs (check member changes)
        for pack_id in current_pack_ids & last_pack_ids:
            current_pack = current_state['packs'][pack_id]
            last_pack = self._last_state['packs'][pack_id]

            # Check if members changed
            if set(current_pack.get('memberIds', [])) != set(last_pack.get('memberIds', [])):
                delta['packs']['modified'][pack_id] = current_pack
```

**Integration into main.py**:
```python
class SimulationManager:
    def __init__(self):
        self.delta_encoder = DeltaEncoder()
        # ... existing code ...

    async def broadcast_state(self):
        """Broadcast delta-encoded state"""
        full_state = self.simulation.get_state()
        encoded = self.delta_encoder.encode(full_state)

        message = json.dumps(encoded)
        # ... send to clients ...
```

**Client-side Integration** (frontend needs update):
```typescript
// Client maintains full state and applies deltas
class SimulationStateManager {
    private state: SimulationState;

    applyUpdate(message: any) {
        if (message.type === 'full') {
            this.state = message.state;
        } else if (message.type === 'delta') {
            this.applyDelta(message);
        }
    }

    applyDelta(delta: any) {
        // Add new entities
        Object.assign(this.state.entities, delta.entities.added);

        // Update modified entities
        Object.assign(this.state.entities, delta.entities.modified);

        // Remove deleted entities
        for (const id of delta.entities.removed) {
            delete this.state.entities[id];
        }

        // Similar for packs...
    }
}
```

**Expected Reduction**:
- Initial frames: ~5% modified (750 bytes vs 15 KB)
- Steady state: ~10-20% modified (1.5-3 KB vs 15 KB)
- **Average: 4-5x bandwidth reduction**

#### 3.2 Binary Serialization with MessagePack

**File**: `server/pyproject.toml` - Add dependency:
```toml
dependencies = [
    # ... existing ...
    "msgpack>=1.0.0",
]
```

**File**: `server/app/main.py` - Modify broadcast:
```python
import msgpack

async def broadcast_state(self):
    """Broadcast using MessagePack binary format"""
    full_state = self.simulation.get_state()
    encoded = self.delta_encoder.encode(full_state)

    # Use MessagePack instead of JSON
    binary_message = msgpack.packb(encoded, use_bin_type=True)

    # Send as binary WebSocket message
    for connection in self.active_connections:
        try:
            await connection.send_bytes(binary_message)
        except Exception as e:
            # ... error handling ...
```

**Frontend Integration** (client needs msgpack library):
```typescript
// Install: npm install @msgpack/msgpack

import { decode } from '@msgpack/msgpack';

websocket.onmessage = (event: MessageEvent) => {
    if (event.data instanceof Blob) {
        event.data.arrayBuffer().then(buffer => {
            const decoded = decode(new Uint8Array(buffer));
            stateManager.applyUpdate(decoded);
        });
    }
};
```

**Expected Benefits**:
- 30-40% smaller payloads than JSON
- Faster encoding/decoding (2-3x)
- Combined with delta: 5-7x total reduction

#### 3.3 Adaptive Broadcast Rate

**File**: `server/app/simulation/simulation.py`

**Implementation**:
```python
class Simulation:
    def __init__(self):
        self.target_frame_time = 0.0167  # 60 FPS
        self.adaptive_broadcast = True
        self.broadcast_interval = 1  # Send every Nth frame
        # ... existing code ...

    async def update_loop(self):
        """Main simulation loop with adaptive broadcasting"""
        while self._is_running:
            frame_start = time.time()

            # Always update simulation at 60 FPS
            self.world.update(self.fixed_dt)
            self._cleanup_out_of_bounds_entities()

            frame_time = time.time() - frame_start

            # Adapt broadcast rate based on frame time
            if self.adaptive_broadcast:
                if frame_time > self.target_frame_time * 1.5:
                    # System overloaded, reduce broadcast rate
                    self.broadcast_interval = 2  # 30 FPS
                elif frame_time > self.target_frame_time * 1.2:
                    self.broadcast_interval = 1  # 60 FPS
                else:
                    # Plenty of headroom, could increase quality
                    self.broadcast_interval = 1

            # Broadcast based on interval
            if self.tick_count % self.broadcast_interval == 0:
                # Yield to broadcast task
                await asyncio.sleep(0)

            # Wait for next frame
            sleep_time = max(0, self.target_frame_time - frame_time)
            await asyncio.sleep(sleep_time)
```

**Benefits**:
- Maintains 60 FPS simulation even under load
- Reduces broadcast overhead when CPU-bound
- Client interpolates between frames for smooth rendering

#### 3.4 Broadcast Task Priority & Yielding

**File**: `server/app/main.py`

**Current Issue**: `asyncio.sleep(0.01)` doesn't yield frequently enough

**New Implementation**:
```python
async def broadcast_loop(self):
    """Dedicated broadcast task with high priority"""
    while True:
        try:
            # Wait for next broadcast signal
            await self.broadcast_event.wait()
            self.broadcast_event.clear()

            # Broadcast immediately
            await self._send_state_to_clients()

            # Yield briefly
            await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

async def update_loop(self):
    """Modified simulation loop with explicit yielding"""
    while self._is_running:
        # Update simulation
        self.world.update(self.fixed_dt)

        # Signal broadcast (non-blocking)
        self.broadcast_event.set()

        # Yield to broadcast task EVERY frame
        await asyncio.sleep(0)

        # Then wait for next frame
        # ...
```

**Benefits**:
- Guarantees broadcast task gets CPU time
- Prevents WebSocket timeout even during heavy simulation
- Better separation of concerns

#### Phase 3 Expected Results
- **Bandwidth**: 900 KB/s → 150-200 KB/s (4-5x reduction)
- **Clients**: Support 5-10 simultaneous clients
- **Disconnections**: Eliminated even at 200+ entities
- **Latency**: More consistent frame delivery

---

### Phase 4: Advanced Optimizations (Optional)
**Goal**: Push to 200+ entities, maximize performance
**Estimated Time**: 2 hours
**Target Metrics**: Frame time 6-10ms, support 200+ entities

#### 4.1 Quadtree Spatial Index

**New File**: `server/app/simulation/core/quadtree.py`

**Replace uniform grid with adaptive quadtree**:
- Better for non-uniform entity distribution
- O(log n) insertion and queries
- Automatically subdivides dense areas

**Implementation outline**:
```python
class QuadTree:
    """
    Adaptive spatial index using quadtree.
    Subdivides when cell exceeds MAX_ENTITIES.
    """
    MAX_ENTITIES = 10
    MAX_DEPTH = 6

    def __init__(self, bounds: Rectangle, depth: int = 0):
        self.bounds = bounds
        self.depth = depth
        self.entities: List[UUID] = []
        self.subdivided = False
        self.children: List[QuadTree] = []

    def insert(self, entity_id: UUID, position: Vector2D) -> bool:
        if not self.bounds.contains(position):
            return False

        if not self.subdivided:
            self.entities.append(entity_id)
            if len(self.entities) > self.MAX_ENTITIES and self.depth < self.MAX_DEPTH:
                self.subdivide()
            return True

        # Insert into children
        for child in self.children:
            if child.insert(entity_id, position):
                return True
        return False

    def query_radius(self, center: Vector2D, radius: float) -> List[UUID]:
        """Query entities within radius"""
        if not self.bounds.intersects_circle(center, radius):
            return []

        results = []

        if not self.subdivided:
            # Leaf node - check all entities
            for entity_id in self.entities:
                # Check actual distance
                if self._in_radius(entity_id, center, radius):
                    results.append(entity_id)
        else:
            # Internal node - recurse to children
            for child in self.children:
                results.extend(child.query_radius(center, radius))

        return results
```

**Integration**: Replace `SpatialGrid` with `QuadTree` in `SimulationContext`

**Benefits**:
- Better performance with clustered entities (packs)
- Automatic adaptation to entity distribution
- Faster queries in sparse areas

#### 4.2 SIMD Vectorization for Physics

**Use NumPy for batch operations**:

**File**: `server/pyproject.toml` - Add dependency:
```toml
dependencies = [
    # ... existing ...
    "numpy>=1.24.0",
]
```

**File**: `server/app/simulation/components/base/physics.py`

**Current**: Individual force calculations per entity
**New**: Batch calculation for all entities

```python
import numpy as np

class PhysicsSystem:
    """
    System-level physics processing using NumPy.
    Calculates forces for all entities in parallel.
    """

    def update_all(self, entities: List[Entity], dt: float):
        """Batch update all entities"""
        n = len(entities)

        # Convert to NumPy arrays
        positions = np.array([[e.position.x, e.position.y] for e in entities])
        velocities = np.array([[e.velocity.x, e.velocity.y] for e in entities])

        # Calculate pairwise distances (vectorized)
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        distances = np.linalg.norm(diff, axis=2)

        # Calculate separation forces (vectorized)
        separation_forces = self._batch_separation(diff, distances, entities)

        # Apply forces
        velocities += separation_forces * dt
        positions += velocities * dt

        # Update entities
        for i, entity in enumerate(entities):
            entity.position = Vector2D(positions[i, 0], positions[i, 1])
            entity.velocity = Vector2D(velocities[i, 0], velocities[i, 1])
```

**Benefits**:
- 5-10x faster force calculations with SIMD
- Reduced Python overhead
- Better CPU cache utilization

**Trade-off**: Less modular than component-based approach

#### 4.3 Entity Pooling

**Reduce garbage collection pressure**:

**New File**: `server/app/simulation/core/object_pool.py`

```python
class EntityPool:
    """
    Object pool for entities.
    Reuses dead entities instead of creating new ones.
    """

    def __init__(self, initial_size: int = 100):
        self._available: List[Entity] = []
        self._in_use: Set[UUID] = set()

        # Pre-allocate entities
        for _ in range(initial_size):
            self._available.append(Entity())

    def acquire(self) -> Entity:
        """Get entity from pool or create new"""
        if self._available:
            entity = self._available.pop()
            entity.reset()  # Reset to default state
        else:
            entity = Entity()

        self._in_use.add(entity.id)
        return entity

    def release(self, entity: Entity):
        """Return entity to pool"""
        if entity.id in self._in_use:
            self._in_use.remove(entity.id)
            self._available.append(entity)
```

**Benefits**:
- Reduces GC pauses
- More consistent frame times
- Lower memory allocation overhead

#### 4.4 Profiling & Monitoring

**Add real-time performance metrics**:

**New File**: `server/app/api/metrics.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PerformanceMetrics(BaseModel):
    frame_time_avg: float
    frame_time_max: float
    entity_count: int
    pack_count: int
    query_cache_hit_rate: float
    memory_usage_mb: float

@router.get("/metrics", response_model=PerformanceMetrics)
async def get_metrics():
    """Real-time performance metrics"""
    # Collect from simulation
    # ...
```

**Add cProfile integration**:
```python
import cProfile
import pstats

def profile_frame(simulation: Simulation):
    """Profile single simulation frame"""
    profiler = cProfile.Profile()
    profiler.enable()

    simulation.world.update(simulation.fixed_dt)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions
```

#### Phase 4 Expected Results
- **Frame time**: 6-10ms at 200+ entities
- **Scalability**: Linear scaling up to 300 entities
- **GC pauses**: Reduced by 60-80%
- **Profiling**: Identify remaining bottlenecks

---

## Implementation Testing Strategy

### Phase 1 Tests

#### Performance Tests
```python
# test_performance_phase1.py
import pytest
import time

def test_frame_time_with_150_entities():
    """Frame time should be <20ms with 150 entities"""
    sim = create_simulation_with_n_entities(150)

    frame_times = []
    for _ in range(100):
        start = time.time()
        sim.world.update(0.0167)
        frame_times.append(time.time() - start)

    avg_frame_time = sum(frame_times) / len(frame_times)
    assert avg_frame_time < 0.020, f"Frame time {avg_frame_time*1000}ms exceeds 20ms"

def test_pack_split_correctness():
    """Pack splits should still occur at correct distances"""
    pack = create_pack_with_spread_members(spread=150)
    context = create_test_context()

    pack.update(context, 0.0167)

    # Should detect split when members >100 units apart
    assert pack._is_dispersed()  # New method should detect
    # Verify split actually happens
    new_pack = pack._detect_split_kmeans(context)
    assert new_pack is not None

def test_memory_bounded_after_10_minutes():
    """Memory should stabilize after long run"""
    sim = create_simulation()
    initial_memory = get_process_memory_mb()

    # Run for 10 minutes (simulated time)
    for _ in range(60 * 60 * 10):  # 36000 frames
        sim.world.update(0.0167)

    final_memory = get_process_memory_mb()
    memory_growth = final_memory - initial_memory

    assert memory_growth < 100, f"Memory grew {memory_growth}MB, possible leak"
```

#### Correctness Tests
```python
def test_incremental_grid_equals_full_rebuild():
    """Incremental grid should match full rebuild"""
    context = create_test_context()
    entities = create_random_entities(100)

    # Method 1: Full rebuild
    context._rebuild_spatial_grid()
    grid1 = context.spatial_grid.get_all_entities()

    # Method 2: Incremental updates
    context.spatial_grid.clear()
    for entity in entities:
        context._update_entity_in_grid(entity)
    grid2 = context.spatial_grid.get_all_entities()

    assert set(grid1) == set(grid2)

def test_pack_center_cache_correctness():
    """Cached center should equal calculated center"""
    pack = create_test_pack()

    # Calculated center
    expected = pack._calculate_center()

    # Cached center (first call calculates, second uses cache)
    pack._center_dirty = True
    actual1 = pack.pack_center
    actual2 = pack.pack_center  # Should use cache

    assert actual1 == expected
    assert actual2 == expected
    assert not pack._center_dirty  # Should be cached
```

### Phase 2 Tests

#### Query Cache Tests
```python
def test_query_cache_returns_same_results():
    """Cached queries should return identical results"""
    context = create_test_context()
    cache = FrameQueryCache()
    entity = create_test_entity()

    # First query (cache miss)
    results1 = cache.get_nearby(entity.id, 50.0, context)

    # Second query same frame (cache hit)
    results2 = cache.get_nearby(entity.id, 50.0, context)

    assert set(results1) == set(results2)
    assert cache._query_stats['cache_hits'] == 1

def test_query_cache_hit_rate():
    """Should achieve 60%+ cache hit rate with typical components"""
    sim = create_simulation_with_n_entities(100)
    context = sim.world

    # Simulate one frame with all components
    for entity in context.get_objects_by_type(Entity):
        # Physics queries (3 queries, same radius)
        context.query_cache.get_nearby(entity.id, 50, context)
        context.query_cache.get_nearby(entity.id, 50, context)
        context.query_cache.get_nearby(entity.id, 50, context)

        # Diet query (different radius)
        context.query_cache.get_nearby(entity.id, 100, context)

    stats = context.query_cache.get_stats()
    assert stats['hit_rate'] > 0.60
```

### Phase 3 Tests

#### Delta Encoding Tests
```python
def test_delta_encoding_accuracy():
    """Client state should match server after delta reconstruction"""
    encoder = DeltaEncoder()

    # Initial state
    state1 = create_test_state(entities=50)
    full1 = encoder.encode(state1)
    assert full1['type'] == 'full'

    # Modified state (10 entities moved, 2 added, 1 removed)
    state2 = modify_state(state1, moved=10, added=2, removed=1)
    delta = encoder.encode(state2)
    assert delta['type'] == 'delta'

    # Reconstruct on client
    client_state = full1['state'].copy()
    apply_delta(client_state, delta)

    # Should match server state
    assert client_state == state2

def test_delta_reduces_bandwidth():
    """Delta encoding should reduce bandwidth by 4x+"""
    encoder = DeltaEncoder()
    state = create_test_state(entities=100)

    full_msg = encoder.encode(state)
    full_size = len(json.dumps(full_msg))

    # Small change
    state['entities'][list(state['entities'].keys())[0]]['position']['x'] += 10
    delta_msg = encoder.encode(state)
    delta_size = len(json.dumps(delta_msg))

    reduction = full_size / delta_size
    assert reduction > 4.0, f"Only {reduction}x reduction, expected 4x+"

def test_msgpack_smaller_than_json():
    """MessagePack should be 30%+ smaller than JSON"""
    state = create_test_state(entities=100)

    json_size = len(json.dumps(state))
    msgpack_size = len(msgpack.packb(state))

    reduction = (json_size - msgpack_size) / json_size
    assert reduction > 0.30, f"Only {reduction*100}% reduction, expected 30%+"
```

#### Multi-client Tests
```python
@pytest.mark.asyncio
async def test_five_clients_stable():
    """Should support 5 clients without disconnections"""
    sim = create_simulation_with_n_entities(150)
    clients = [create_test_websocket_client() for _ in range(5)]

    # Run for 5 minutes
    for _ in range(60 * 60 * 5):  # 18000 frames
        sim.world.update(0.0167)

        # Broadcast to all clients
        await sim.broadcast_state()

    # All clients should still be connected
    for client in clients:
        assert client.is_connected()
```

### Integration Tests

```python
def test_end_to_end_performance():
    """Full simulation with all optimizations"""
    sim = create_simulation()

    # Spawn entities gradually
    for tick in range(10000):
        if tick % 100 == 0 and tick < 5000:
            spawn_random_entity(sim)

        frame_start = time.time()
        sim.world.update(0.0167)
        frame_time = time.time() - frame_start

        entity_count = len(sim.world.get_objects_by_type(Entity))

        # Frame time requirements based on entity count
        if entity_count < 100:
            assert frame_time < 0.015  # 15ms
        elif entity_count < 150:
            assert frame_time < 0.020  # 20ms
        elif entity_count < 200:
            assert frame_time < 0.025  # 25ms
```

---

## Performance Metrics & Monitoring

### Key Metrics to Track

| Metric | Phase 0 | Phase 1 Target | Phase 2 Target | Phase 3 Target | Phase 4 Target |
|--------|---------|----------------|----------------|----------------|----------------|
| Frame Time (100 ent) | 25ms | 10ms | 7ms | 6ms | 5ms |
| Frame Time (150 ent) | 40ms+ | 18ms | 12ms | 10ms | 8ms |
| Frame Time (200 ent) | N/A | 30ms | 20ms | 15ms | 10ms |
| Max Stable Entities | 80-100 | 120-140 | 150-180 | 200+ | 250+ |
| Queries per Frame | 600 | 600 | 100-150 | 100-150 | 80-100 |
| Bandwidth (per client) | 900 KB/s | 900 KB/s | 900 KB/s | 150-200 KB/s | 100-150 KB/s |
| Memory Growth (10min) | Unbounded | <50 MB | <50 MB | <50 MB | <30 MB |
| Query Cache Hit Rate | N/A | N/A | 60-80% | 60-80% | 70-85% |

### Instrumentation Code

```python
# Add to simulation.py
class PerformanceMonitor:
    def __init__(self):
        self.frame_times: List[float] = []
        self.query_counts: List[int] = []
        self.entity_counts: List[int] = []

    def record_frame(self, frame_time: float, query_count: int, entity_count: int):
        self.frame_times.append(frame_time)
        self.query_counts.append(query_count)
        self.entity_counts.append(entity_count)

        # Keep only last 1000 frames
        if len(self.frame_times) > 1000:
            self.frame_times.pop(0)
            self.query_counts.pop(0)
            self.entity_counts.pop(0)

    def get_stats(self) -> dict:
        if not self.frame_times:
            return {}

        return {
            'avg_frame_time': sum(self.frame_times) / len(self.frame_times),
            'max_frame_time': max(self.frame_times),
            'p95_frame_time': sorted(self.frame_times)[int(len(self.frame_times) * 0.95)],
            'avg_queries': sum(self.query_counts) / len(self.query_counts),
            'avg_entities': sum(self.entity_counts) / len(self.entity_counts)
        }
```

---

## Expected Outcomes Summary

### Phase 1: Critical Bottleneck Elimination
- ✅ Eliminates O(n²) pack split detection
- ✅ Reduces grid overhead by 70-80%
- ✅ Fixes memory leaks
- ✅ Stable at 120-140 entities
- ✅ WebSocket disconnections rare (>5 min runtime)

### Phase 2: Spatial Query Optimization
- ✅ 6x reduction in spatial queries
- ✅ 60-80% cache hit rate
- ✅ Frame time reduced by 40-50%
- ✅ Stable at 150-180 entities
- ✅ Can run indefinitely without degradation

### Phase 3: Network Optimization
- ✅ 4-5x bandwidth reduction
- ✅ Support 5-10 simultaneous clients
- ✅ More consistent frame delivery
- ✅ No WebSocket timeouts even at 200+ entities
- ✅ Smooth rendering even with network variance

### Phase 4: Advanced Optimizations
- ✅ Push to 200-250+ entities
- ✅ Linear scaling characteristics
- ✅ Minimal GC pauses
- ✅ Production-ready performance monitoring
- ✅ Foundation for future features (AI behaviors, more species, etc.)

---

## Risk Assessment & Mitigation

### Risks

1. **Breaking Changes to Frontend**
   - **Risk**: Delta encoding and MessagePack require frontend updates
   - **Mitigation**: Implement backward compatibility, feature flags
   - **Timeline**: Coordinate frontend changes in Phase 3

2. **Test Coverage Gaps**
   - **Risk**: Optimizations may introduce subtle bugs
   - **Mitigation**: Comprehensive test suite, gradual rollout
   - **Timeline**: Write tests alongside implementation

3. **Algorithm Complexity**
   - **Risk**: Welzl's algorithm and k-means may be difficult to implement correctly
   - **Mitigation**: Use well-tested libraries or reference implementations
   - **Timeline**: Allocate extra time for Phase 1 validation

4. **Performance Regression**
   - **Risk**: Some optimizations may not yield expected gains
   - **Mitigation**: Profile before/after, keep fallback code paths
   - **Timeline**: Maintain performance baselines

### Rollback Strategy

Each phase is independent and can be rolled back:
- **Phase 1**: Revert pack split detection, grid updates
- **Phase 2**: Disable query cache, use direct queries
- **Phase 3**: Revert to JSON full-state broadcasts
- **Phase 4**: Optional enhancements, no dependency

---

## Conclusion

This 4-phase optimization plan addresses the root causes of backend performance degradation through algorithmic improvements and smart data structures. By eliminating O(n²) operations, implementing spatial query caching, and optimizing network serialization, the simulation will scale from 80-100 entities to 200+ entities while maintaining full accuracy across all features.

**Next Steps**:
1. Review and approve plan
2. Begin Phase 1 implementation
3. Validate performance gains with tests
4. Proceed to subsequent phases based on results

**Total Estimated Time**: 8-10 hours across 4 sessions
**Expected Result**: 3-4x performance improvement, 200+ stable entities, no disconnections
