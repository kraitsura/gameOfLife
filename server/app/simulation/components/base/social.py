from typing import Dict, Optional, Set, TYPE_CHECKING
from collections import OrderedDict
from app.simulation.core.interfaces import Component
from app.simulation.core import PHYSICS_CONFIG
import logging

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class SocialComponent(Component):
    """
    Handles pack formation and social interactions between entities.

    Entities form packs when they:
    1. Build familiarity through multiple interactions (collisions, feeding nearby, etc.)
    2. Stay close to same-species entities for a duration

    Pack membership provides benefits in combat and other interactions.
    """

    # Class constants for pack formation (very strict requirements for meaningful packs)
    COLLISION_DISTANCE = 3.0  # Distance for close encounters that build familiarity (must nearly touch)
    FAMILIARITY_THRESHOLD = 13.0  # Minimum interactions needed to form pack (12-15 range, very strict)
    PACK_FORMATION_TIME = 8.0  # Time (seconds) entities must stay close to form pack (increased from 5.0)
    INTERACTION_COOLDOWN = 1.0  # Cooldown between counting same interaction type (seconds)
    MAX_PACK_MEMBER_DISTANCE_MULTIPLIER = 1.5  # Max distance = vision * this (tighter cohesion than before)

    # Memory management constants (Phase 1 optimization)
    MAX_INTERACTIONS = 50  # Maximum tracked interactions per entity
    INTERACTION_TTL = 60.0  # Seconds before interaction expires

    def __init__(self, pack_mentality: float = 0.5):
        self.pack_mentality = pack_mentality
        self.pack_id: Optional[str] = None
        self.time_in_pack = 0.0
        self.leadership_score = 0.0

        # Track proximity time with potential pack members
        self.proximity_timers: Dict[str, float] = {}  # entity_id -> time_near
        self.relationships: Dict[str, float] = {}  # entity_id -> relationship_strength

        # Familiarity system with LRU caching (Phase 1 optimization)
        self.familiarity_scores: OrderedDict[str, float] = OrderedDict()  # entity_id -> interaction_count
        self.last_interaction_time: OrderedDict[str, float] = OrderedDict()  # entity_id -> last_interaction_timestamp
        self.current_time: float = 0.0  # Track accumulated time for cooldowns

    def _prune_old_interactions(self) -> None:
        """
        Remove interactions older than TTL (Phase 1 optimization).
        Prevents unbounded memory growth.
        """
        to_remove = []
        for entity_id, last_time in self.last_interaction_time.items():
            if self.current_time - last_time > self.INTERACTION_TTL:
                to_remove.append(entity_id)

        for entity_id in to_remove:
            self.familiarity_scores.pop(entity_id, None)
            self.last_interaction_time.pop(entity_id, None)

        if to_remove:
            logging.debug(f"Pruned {len(to_remove)} old interactions")

    def record_interaction(self, entity_id: str, interaction_weight: float = 1.0) -> bool:
        """
        Record an interaction with another entity to build familiarity.

        Interactions include: close proximity, feeding nearby, cooperative hunting, etc.
        Has a cooldown to prevent spam-counting the same interaction repeatedly.
        Implements LRU caching with bounded memory (Phase 1 optimization).

        Args:
            entity_id: ID of the entity we interacted with
            interaction_weight: How much this interaction contributes to familiarity
                                (1.0 = full interaction, 0.5 = minor interaction)

        Returns:
            True if interaction was recorded, False if on cooldown
        """
        # Prune old interactions first (Phase 1 optimization)
        self._prune_old_interactions()

        # Check cooldown
        last_time = self.last_interaction_time.get(entity_id, -float('inf'))
        if self.current_time - last_time < self.INTERACTION_COOLDOWN:
            return False

        # LRU eviction if at capacity (Phase 1 optimization)
        if len(self.familiarity_scores) >= self.MAX_INTERACTIONS:
            if entity_id not in self.familiarity_scores:
                # Remove oldest (first in OrderedDict)
                self.familiarity_scores.popitem(last=False)
                self.last_interaction_time.popitem(last=False)
                logging.debug(f"LRU eviction: removed oldest interaction")

        # Record the interaction
        current_familiarity = self.familiarity_scores.get(entity_id, 0.0)
        self.familiarity_scores[entity_id] = current_familiarity + interaction_weight
        self.last_interaction_time[entity_id] = self.current_time

        # Move to end (mark as recently used) for LRU
        self.familiarity_scores.move_to_end(entity_id)
        self.last_interaction_time.move_to_end(entity_id)

        logging.debug(
            f"Entity interaction recorded with {entity_id}: "
            f"familiarity now {self.familiarity_scores[entity_id]:.1f}"
        )
        return True

    def reset_familiarity(self) -> None:
        """
        Reset all familiarity scores and interaction data.

        Called when an entity leaves a pack to ensure they must rebuild
        familiarity from scratch before joining/forming another pack.
        """
        self.familiarity_scores.clear()
        self.last_interaction_time.clear()
        self.proximity_timers.clear()
        self.relationships.clear()
        logging.debug("Familiarity scores and timers reset")

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """
        Update social behavior and pack formation.

        1. Update current time for cooldowns
        2. Query nearby same-species entities (vision-based distance)
        3. Track collision-based familiarity building
        4. Track proximity time
        5. Form pack if entities have sufficient familiarity AND proximity time
        6. Update pack membership
        """
        from app.simulation.models import Pack
        from app.simulation.models.entity import EntityState

        # Don't update if already dead
        if owner.state == EntityState.DEAD:
            return

        # Update time tracker for cooldowns
        self.current_time += dt

        # If already in a pack, update pack time
        if owner.pack_id:
            self.pack_id = owner.pack_id
            self.time_in_pack += dt
            self._update_pack_relationships(owner, context, dt)
            return

        # Use half of entity's vision range for pack formation distance (tighter formation requirement)
        formation_distance = owner.stats.entity_vision * 0.5

        # Find nearby same-species entities for potential pack formation (Phase 2: use query cache)
        nearby_entities = context.query_cache.get_nearby(
            owner.id,
            formation_distance,
            context
        )

        # Filter to same species only
        same_species_nearby = []
        for entity in nearby_entities:
            if hasattr(entity, 'species_id') and entity.species_id == owner.species_id:
                same_species_nearby.append(entity)

        if not same_species_nearby:
            # Reset proximity timers if no one nearby
            self.proximity_timers.clear()
            return

        # Update proximity timers and check for collisions (familiarity building)
        current_nearby_ids = set()
        for entity in same_species_nearby:
            current_nearby_ids.add(entity.id)

            # Calculate distance to entity
            distance = (entity.position - owner.position).magnitude()

            # Check for close collision to build familiarity
            if distance < self.COLLISION_DISTANCE:
                # Record collision as interaction (weight 1.0 = full interaction)
                self.record_interaction(entity.id, interaction_weight=1.0)

            # Increment proximity timer for entities that are nearby
            if entity.id not in self.proximity_timers:
                self.proximity_timers[entity.id] = 0.0
            self.proximity_timers[entity.id] += dt

        # Remove timers for entities no longer nearby
        ids_to_remove = [eid for eid in self.proximity_timers if eid not in current_nearby_ids]
        for eid in ids_to_remove:
            del self.proximity_timers[eid]

        # Check if we should form a pack
        # Entities must meet BOTH requirements:
        # 1. Sufficient familiarity (multiple interactions)
        # 2. Sufficient proximity time (stayed close)
        potential_pack_members = []
        for entity in same_species_nearby:
            has_familiarity = self.familiarity_scores.get(entity.id, 0.0) >= self.FAMILIARITY_THRESHOLD
            has_proximity_time = self.proximity_timers.get(entity.id, 0.0) >= self.PACK_FORMATION_TIME

            if has_familiarity and has_proximity_time:
                potential_pack_members.append(entity)
                logging.debug(
                    f"Entity {entity.id} qualifies for pack: "
                    f"familiarity={self.familiarity_scores.get(entity.id, 0.0):.1f}, "
                    f"proximity_time={self.proximity_timers.get(entity.id, 0.0):.1f}s"
                )

        if potential_pack_members:
            # Prevent immediate pack combining - check if potential members are in different packs
            pack_ids_found = set()
            packless_members = []

            for member in potential_pack_members:
                if member.pack_id:
                    pack_ids_found.add(member.pack_id)
                else:
                    packless_members.append(member)

            # Case 1: All potential members are in the SAME existing pack - join it
            if len(pack_ids_found) == 1:
                existing_pack_id = next(iter(pack_ids_found))
                existing_pack = context.get_by_id(Pack, existing_pack_id)
                if existing_pack:
                    owner.pack_id = existing_pack.id
                    self.pack_id = existing_pack.id
                    existing_pack.members.add(owner)
                    logging.info(
                        f"Entity {owner.id} joined existing pack {existing_pack.id} "
                        f"(all potential members in same pack)"
                    )

            # Case 2: Potential members in MULTIPLE packs - don't join yet, let pack-level merging handle it
            elif len(pack_ids_found) > 1:
                logging.debug(
                    f"Entity {owner.id} found {len(potential_pack_members)} familiar entities "
                    f"in {len(pack_ids_found)} different packs - waiting for pack-level merge"
                )
                # Don't form/join pack - let pack interaction system handle merging

            # Case 3: No existing packs (all packless) - form new pack
            elif len(pack_ids_found) == 0:
                pack_members = [owner] + potential_pack_members
                new_pack = Pack(pack_members)
                context.register(new_pack)

                # Assign pack ID to all members
                for member in pack_members:
                    member.pack_id = new_pack.id
                    social = member.get_component('SocialComponent')
                    if social:
                        social.pack_id = new_pack.id

                logging.info(f"New pack {new_pack.id} formed with {len(pack_members)} members")

    def _update_pack_relationships(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """Update relationships with pack members"""
        from app.simulation.models import Pack

        pack = context.get_by_id(Pack, self.pack_id)
        if not pack:
            # Pack no longer exists, clear pack ID and reset familiarity
            owner.pack_id = None
            self.pack_id = None
            self.time_in_pack = 0.0
            self.reset_familiarity()
            logging.info(f"Entity {owner.id} left pack, familiarity reset")
            return

        # Update relationships with pack members
        for member in pack.members:
            if member.id != owner.id:
                current_relationship = self.relationships.get(member.id, 0.0)
                # Strengthen relationships over time (max 1.0)
                self.relationships[member.id] = min(1.0, current_relationship + 0.01 * dt)
