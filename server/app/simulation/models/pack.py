from typing import List, Set, Dict, Optional, Tuple, TYPE_CHECKING
from uuid import uuid4
from app.simulation.core.interfaces import GameObject
from app.simulation.core.vector import Vector2D
from app.simulation.models import Entity
import logging

if TYPE_CHECKING:
    from app.simulation.core.context import SimulationContext

class Pack(GameObject):
    """
    Pack of entities that hunt, travel, and interact together.

    Features:
    - Member distance monitoring and removal
    - Pack splitting when groups diverge
    - Pack-to-pack interaction tracking
    - Conditional merging based on size or familiarity
    """

    # Pack management constants (very strict for meaningful pack cohesion)
    MAX_MEMBER_DISTANCE_MULTIPLIER = 1.5  # Max distance = avg_vision * this (tighter cohesion)
    MEMBER_TIMEOUT = 4.0  # Seconds a member can be too far before removal (faster ejection)
    PACK_SPLIT_MIN_CLUSTER_RATIO = 0.3  # Min 30% of pack to form new pack
    PACK_SPLIT_DISTANCE_THRESHOLD = 100.0  # Min distance between clusters to split
    PACK_MERGE_SIZE_RATIO = 3.0  # Larger pack must be 3x+ bigger to absorb (harder to merge)
    PACK_MERGE_FAMILIARITY = 17.0  # Interaction score needed for equal-size merge (much stricter)
    PACK_INTERACTION_COOLDOWN = 2.0  # Cooldown for pack-level interactions

    # Memory management constants (Phase 1 optimization)
    MAX_PACK_INTERACTION_AGE = 120.0  # Seconds before pack interaction expires
    PACK_VALIDATION_INTERVAL = 10.0  # Seconds between validation checks

    def __init__(self, members: List[Entity]):
        self.id = str(uuid4())
        self.members: Set[Entity] = set(members)

        # Member distance tracking
        self.member_distance_timers: Dict[str, float] = {}  # entity_id -> time_too_far

        # Pack center caching (Phase 1 optimization)
        self._cached_center: Optional[Vector2D] = None
        self._center_dirty: bool = True

        # Pack split throttling (Phase 1 optimization)
        self._last_split_check: float = 0.0
        self.SPLIT_CHECK_INTERVAL = 0.5  # Only check split every 0.5 seconds

        # Pack-to-pack interaction tracking
        self.pack_interactions: Dict[str, float] = {}  # pack_id -> interaction_score
        self.last_pack_interaction: Dict[str, float] = {}  # pack_id -> last_time
        self.current_time: float = 0.0  # Accumulated time for cooldowns

        # Memory management (Phase 1 optimization)
        self._last_validation: float = 0.0  # Last time we validated pack interactions

    @property
    def pack_center(self) -> Vector2D:
        """
        Get pack center with caching (Phase 1 optimization).

        Returns cached center if valid, otherwise recalculates.
        """
        if self._center_dirty or self._cached_center is None:
            self._cached_center = self._calculate_pack_center()
            self._center_dirty = False
        return self._cached_center

    def _invalidate_center(self) -> None:
        """Mark pack center cache as dirty (needs recalculation)."""
        self._center_dirty = True

    def _calculate_pack_center(self) -> Vector2D:
        """
        Calculate the geometric center of the pack.

        Uses majority voting: if pack has clear clusters, the larger cluster
        defines the center (democratic pack center).

        Returns:
            Vector2D representing the pack's center point
        """
        if not self.members:
            return Vector2D(0, 0)

        # Simple geometric center (mean position)
        total_x = 0.0
        total_y = 0.0
        for member in self.members:
            total_x += member.position.x
            total_y += member.position.y

        count = len(self.members)
        return Vector2D(total_x / count, total_y / count)

    def _is_dispersed(self) -> bool:
        """
        Quick O(n) check if pack members are dispersed enough to warrant split check.

        Uses bounding box method - much faster than pairwise distances.
        Returns True if pack might need splitting.
        """
        if len(self.members) < 4:
            return False

        # Calculate bounding box
        positions = [m.position for m in self.members]
        min_x = min(p.x for p in positions)
        max_x = max(p.x for p in positions)
        min_y = min(p.y for p in positions)
        max_y = max(p.y for p in positions)

        # Check if bounding box exceeds split threshold
        max_dimension = max(max_x - min_x, max_y - min_y)

        # Use 1.5x threshold for quick check (conservative)
        return max_dimension > self.PACK_SPLIT_DISTANCE_THRESHOLD * 1.5

    def _check_member_distances(self, context: 'SimulationContext', dt: float) -> None:
        """
        Check if any members are too far from pack center for too long.

        Members beyond 2x vision range for more than MEMBER_TIMEOUT seconds
        are removed from the pack.

        Args:
            context: Simulation context
            dt: Delta time
        """
        if not self.members:
            return

        # Calculate average vision range for the pack
        avg_vision = sum(m.stats.entity_vision for m in self.members) / len(self.members)
        max_distance = avg_vision * self.MAX_MEMBER_DISTANCE_MULTIPLIER

        # Use cached pack center (Phase 1 optimization)
        center = self.pack_center

        # Check each member's distance
        members_to_remove = []
        for member in self.members:
            distance = (member.position - center).magnitude()

            if distance > max_distance:
                # Member is too far - increment their timer
                if member.id not in self.member_distance_timers:
                    self.member_distance_timers[member.id] = 0.0
                self.member_distance_timers[member.id] += dt

                # Check if they've been too far for too long
                if self.member_distance_timers[member.id] >= self.MEMBER_TIMEOUT:
                    members_to_remove.append(member)
                    logging.info(
                        f"Removing member {member.id} from pack {self.id}: "
                        f"too far ({distance:.1f} > {max_distance:.1f}) for "
                        f"{self.member_distance_timers[member.id]:.1f}s"
                    )
            else:
                # Member is within range - reset their timer
                self.member_distance_timers.pop(member.id, None)

        # Remove distant members and reset their familiarity
        for member in members_to_remove:
            self.members.discard(member)
            member.pack_id = None
            self.member_distance_timers.pop(member.id, None)
            self._invalidate_center()  # Cache invalidation (Phase 1 optimization)

            # Reset member's familiarity so they must rebuild relationships
            social = member.get_component('SocialComponent')
            if social:
                social.reset_familiarity()
                logging.info(f"Member {member.id} ejected from pack {self.id}, familiarity reset")

    def _detect_pack_split(self) -> Optional[Tuple[Set[Entity], Set[Entity]]]:
        """
        Detect if pack has split into two distinct groups using spatial clustering.

        Uses optimized 2-means clustering (Phase 1 optimization):
        1. Find two seeds using extreme positions (O(n) instead of O(n²))
        2. Assign each member to nearest center
        3. Check if both clusters meet minimum size requirement
        4. Check if clusters are far enough apart

        Returns:
            Tuple of (cluster1, cluster2) if split detected, None otherwise
        """
        if len(self.members) < 4:  # Need at least 4 members to consider splitting
            return None

        member_list = list(self.members)

        # Find seeds using extreme positions (O(n) - Phase 1 optimization)
        # This replaces the O(n²) pairwise distance check
        min_x_member = min(member_list, key=lambda m: m.position.x)
        max_x_member = max(member_list, key=lambda m: m.position.x)
        min_y_member = min(member_list, key=lambda m: m.position.y)
        max_y_member = max(member_list, key=lambda m: m.position.y)

        # Choose the pair with greater separation
        x_dist = abs(max_x_member.position.x - min_x_member.position.x)
        y_dist = abs(max_y_member.position.y - min_y_member.position.y)

        if x_dist > y_dist:
            seed1, seed2 = min_x_member, max_x_member
            max_distance = x_dist
        else:
            seed1, seed2 = min_y_member, max_y_member
            max_distance = y_dist

        # If the extreme members aren't far apart, no split
        if max_distance < self.PACK_SPLIT_DISTANCE_THRESHOLD:
            return None

        # Assign each member to nearest seed
        cluster1: Set[Entity] = set()
        cluster2: Set[Entity] = set()

        for member in self.members:
            dist1 = (member.position - seed1.position).magnitude()
            dist2 = (member.position - seed2.position).magnitude()

            if dist1 < dist2:
                cluster1.add(member)
            else:
                cluster2.add(member)

        # Check if both clusters meet minimum size requirement
        min_cluster_size = int(len(self.members) * self.PACK_SPLIT_MIN_CLUSTER_RATIO)

        if len(cluster1) < min_cluster_size or len(cluster2) < min_cluster_size:
            return None

        # Clusters are large enough and far apart - split detected!
        logging.info(
            f"Pack {self.id} split detected: "
            f"cluster1={len(cluster1)}, cluster2={len(cluster2)}, "
            f"distance={max_distance:.1f}"
        )
        return (cluster1, cluster2)

    def record_pack_interaction(self, other_pack_id: str) -> bool:
        """
        Record an interaction with another pack to build familiarity.

        Pack interactions occur when members of different packs are near each other.
        Has a cooldown to prevent spam-counting.

        Args:
            other_pack_id: ID of the other pack

        Returns:
            True if interaction was recorded, False if on cooldown
        """
        # Check cooldown
        last_time = self.last_pack_interaction.get(other_pack_id, -float('inf'))
        if self.current_time - last_time < self.PACK_INTERACTION_COOLDOWN:
            return False

        # Record the interaction
        current_score = self.pack_interactions.get(other_pack_id, 0.0)
        self.pack_interactions[other_pack_id] = current_score + 1.0
        self.last_pack_interaction[other_pack_id] = self.current_time

        logging.debug(
            f"Pack {self.id} interaction with pack {other_pack_id}: "
            f"familiarity now {self.pack_interactions[other_pack_id]:.1f}"
        )
        return True

    def _prune_old_pack_interactions(self) -> None:
        """
        Remove pack interactions older than MAX_PACK_INTERACTION_AGE (Phase 1 optimization).
        Prevents unbounded memory growth.
        """
        to_remove = []
        for pack_id, last_time in self.last_pack_interaction.items():
            if self.current_time - last_time > self.MAX_PACK_INTERACTION_AGE:
                to_remove.append(pack_id)

        for pack_id in to_remove:
            self.pack_interactions.pop(pack_id, None)
            self.last_pack_interaction.pop(pack_id, None)

        if to_remove:
            logging.debug(f"Pack {self.id} pruned {len(to_remove)} old pack interactions")

    def _validate_pack_interactions(self, context: 'SimulationContext') -> None:
        """
        Remove references to non-existent packs (Phase 1 optimization).
        Prevents dangling references when packs are deleted.
        """
        to_remove = []
        for pack_id in list(self.pack_interactions.keys()):
            # Check if pack still exists
            if not context.get_by_id(Pack, pack_id):
                to_remove.append(pack_id)

        for pack_id in to_remove:
            self.pack_interactions.pop(pack_id, None)
            self.last_pack_interaction.pop(pack_id, None)

        if to_remove:
            logging.debug(f"Pack {self.id} removed {len(to_remove)} dangling pack references")

    def cleanup_references(self, context: 'SimulationContext') -> None:
        """
        Called when pack is being deleted (Phase 1 optimization).
        Removes this pack from other packs' interaction histories.
        """
        all_packs = context.get_objects_by_type(Pack)
        for pack in all_packs:
            if pack.id != self.id:
                pack.pack_interactions.pop(self.id, None)
                pack.last_pack_interaction.pop(self.id, None)

    def should_merge_with(self, other_pack: 'Pack') -> bool:
        """
        Determine if this pack should merge with another pack.

        Conditions for merging:
        1. Size ratio: One pack is 2x+ larger (dominant absorbs smaller)
        2. OR pack familiarity: Packs have built sufficient trust (≥10 interactions)

        Args:
            other_pack: The other pack to consider merging with

        Returns:
            True if packs should merge
        """
        if not self.members or not other_pack.members:
            return False

        # Check size ratio
        size1 = len(self.members)
        size2 = len(other_pack.members)
        larger = max(size1, size2)
        smaller = min(size1, size2)

        size_ratio = larger / smaller if smaller > 0 else float('inf')

        # Condition 1: Size difference (larger absorbs smaller)
        if size_ratio >= self.PACK_MERGE_SIZE_RATIO:
            logging.info(
                f"Pack merge approved (size): {self.id}({size1}) + {other_pack.id}({size2}), "
                f"ratio={size_ratio:.1f}"
            )
            return True

        # Condition 2: Pack familiarity (built trust over time)
        familiarity = self.pack_interactions.get(other_pack.id, 0.0)
        if familiarity >= self.PACK_MERGE_FAMILIARITY:
            logging.info(
                f"Pack merge approved (familiarity): {self.id} + {other_pack.id}, "
                f"familiarity={familiarity:.1f}"
            )
            return True

        return False

    def merge_with(self, other_pack: 'Pack', context: 'SimulationContext') -> None:
        """
        Merge another pack into this pack.

        Transfers all members and interaction scores from the other pack.
        The other pack is unregistered from the context.

        Args:
            other_pack: The pack to absorb
            context: Simulation context
        """
        # Transfer members
        for member in other_pack.members:
            self.members.add(member)
            member.pack_id = self.id

        # Invalidate pack center cache (Phase 1 optimization)
        self._invalidate_center()

        # Transfer pack interaction scores
        for pack_id, score in other_pack.pack_interactions.items():
            if pack_id == self.id:
                continue  # Skip self-reference
            current_score = self.pack_interactions.get(pack_id, 0.0)
            # Average the familiarity scores
            self.pack_interactions[pack_id] = (current_score + score) / 2.0

        logging.info(
            f"Pack {self.id} absorbed pack {other_pack.id}: "
            f"new size={len(self.members)}"
        )

        # Unregister the absorbed pack
        context.unregister(other_pack)

    def update(self, context: 'SimulationContext', dt: float) -> None:
        """
        Update pack-level state with comprehensive pack management.

        Handles:
        - Dead member removal
        - Member distance monitoring and removal
        - Pack splitting when groups diverge
        - Pack-to-pack interaction tracking
        - Conditional pack merging
        - Pack dissolution if too small

        Note: Pack members (entities) are already updated by SimulationContext.update().
        This method should only handle pack-level behaviors, not individual member updates.
        """
        from app.simulation.models.entity import EntityState

        # Update time tracker
        self.current_time += dt

        # Periodic cleanup and validation (Phase 1 optimization)
        if self.current_time - self._last_validation >= self.PACK_VALIDATION_INTERVAL:
            self._last_validation = self.current_time
            self._prune_old_pack_interactions()
            self._validate_pack_interactions(context)

        # Remove dead members from pack
        dead_members = [m for m in self.members if m.state == EntityState.DEAD]
        if dead_members:
            for dead_member in dead_members:
                self.members.discard(dead_member)
                dead_member.pack_id = None
            # Invalidate center cache if members were removed (Phase 1 optimization)
            self._invalidate_center()

        # Dissolve pack if too small (need at least 2 members for a pack)
        if len(self.members) < 2:
            for member in list(self.members):
                member.pack_id = None
                # Reset familiarity for all remaining members
                social = member.get_component('SocialComponent')
                if social:
                    social.reset_familiarity()
            self.members.clear()
            # Clean up references before unregistering (Phase 1 optimization)
            self.cleanup_references(context)
            context.unregister(self)
            logging.info(f"Pack {self.id} dissolved: too few members, familiarity reset for all")
            return

        # Check member distances and remove stragglers
        self._check_member_distances(context, dt)

        # Check again after distance removal
        if len(self.members) < 2:
            for member in list(self.members):
                member.pack_id = None
                # Reset familiarity for all remaining members
                social = member.get_component('SocialComponent')
                if social:
                    social.reset_familiarity()
            self.members.clear()
            # Clean up references before unregistering (Phase 1 optimization)
            self.cleanup_references(context)
            context.unregister(self)
            logging.info(f"Pack {self.id} dissolved after distance check, familiarity reset for all")
            return

        # Detect and handle pack splitting (Phase 1 optimization: throttled)
        # Only check split every SPLIT_CHECK_INTERVAL seconds, not every frame
        if self.current_time - self._last_split_check >= self.SPLIT_CHECK_INTERVAL:
            self._last_split_check = self.current_time

            # Quick O(n) dispersal check before expensive split detection
            if self._is_dispersed():
                split_result = self._detect_pack_split()
                if split_result:
                    cluster1, cluster2 = split_result

                    # Determine which cluster is larger (stays as current pack)
                    if len(cluster1) >= len(cluster2):
                        majority, minority = cluster1, cluster2
                    else:
                        majority, minority = cluster2, cluster1

                    # Create new pack with minority cluster
                    new_pack = Pack(list(minority))
                    context.register(new_pack)

                    # Update members in new pack
                    for member in minority:
                        member.pack_id = new_pack.id

                    # Keep majority in current pack
                    self.members = majority
                    for member in majority:
                        member.pack_id = self.id

                    # Invalidate center cache after split
                    self._invalidate_center()

                    logging.info(
                        f"Pack {self.id} split into {self.id}({len(majority)}) "
                        f"and {new_pack.id}({len(minority)})"
                    )

        # Detect nearby packs and record interactions
        if self.members:
            # Calculate average vision for interaction detection
            avg_vision = sum(m.stats.entity_vision for m in self.members) / len(self.members)
            interaction_range = avg_vision * 2.0

            # Get species ID from any member (all pack members are same species)
            species_id = next(iter(self.members)).species_id

            # Find nearby entities using cached pack center (Phase 1 optimization)
            center = self.pack_center
            nearby_entities = context.query_nearby_entities(
                center,
                interaction_range,
                exclude_id=None
            )

            # Track which other packs we're near
            nearby_pack_ids = set()
            for entity in nearby_entities:
                # Check if entity is from same species but different pack
                if (hasattr(entity, 'species_id') and entity.species_id == species_id and
                    hasattr(entity, 'pack_id') and entity.pack_id and
                    entity.pack_id != self.id):
                    nearby_pack_ids.add(entity.pack_id)

            # Record interactions with nearby packs
            for pack_id in nearby_pack_ids:
                self.record_pack_interaction(pack_id)

            # Check for merge opportunities with nearby packs
            for pack_id in nearby_pack_ids:
                other_pack = context.get_by_id(Pack, pack_id)
                if other_pack and self.should_merge_with(other_pack):
                    # Larger pack absorbs smaller (or self if equal size)
                    if len(self.members) >= len(other_pack.members):
                        self.merge_with(other_pack, context)
                    else:
                        other_pack.merge_with(self, context)
                        # Self was absorbed, stop processing
                        return

    def serialize(self) -> dict:
        """Serialize pack to camelCase format for frontend compatibility"""
        return {
            "id": str(self.id),
            "memberIds": [str(member.id) for member in self.members]
        }
