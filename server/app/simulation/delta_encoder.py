"""
Delta state encoder for efficient network transmission (Phase 3 optimization).

Instead of sending the full simulation state every frame, only sends changes
(added/modified/removed entities and packs). This dramatically reduces
bandwidth usage, especially as the simulation stabilizes.
"""

import hashlib
import json
from typing import Dict, Set, Any, List

class DeltaEncoder:
    """
    Encodes simulation state as deltas (changes only).

    Tracks the last state sent to clients and computes differences.
    Periodically sends full state to handle new connections and drift.
    """

    def __init__(self):
        # Last state sent to clients
        self._last_state: Dict[str, Dict] = {
            'entities': {},
            'packs': {},
            'species': {}
        }

        # Quick change detection via hashing
        self._entity_hashes: Dict[str, str] = {}
        self._pack_hashes: Dict[str, str] = {}

        # Frame counter
        self._frame_counter: int = 0

        # Send full state every N frames (5 seconds at 60 FPS)
        self.full_state_interval: int = 300

    def _hash_entity(self, entity_data: dict) -> str:
        """
        Quick hash of entity state for change detection.

        Only hashes frequently changing fields (position, health, energy)
        to detect meaningful changes.
        """
        key_data = {
            'x': round(entity_data.get('x', 0), 1),
            'y': round(entity_data.get('y', 0), 1),
            'vx': round(entity_data.get('vx', 0), 1),
            'vy': round(entity_data.get('vy', 0), 1),
            'health': round(entity_data.get('health', 0), 1),
            'energy': round(entity_data.get('energy', 0), 1),
            'pack': entity_data.get('packId')
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _hash_pack(self, pack_data: dict) -> str:
        """Quick hash of pack state (member list)."""
        member_ids = sorted(pack_data.get('memberIds', []))
        return hashlib.md5(json.dumps(member_ids).encode()).hexdigest()

    def encode(self, current_state: dict) -> dict:
        """
        Encode state as delta or full update.

        Args:
            current_state: Full simulation state

        Returns:
            Delta-encoded state or full state (periodically)
        """
        self._frame_counter += 1

        # Send full state periodically for new connections and to prevent drift
        if self._frame_counter % self.full_state_interval == 0:
            self._last_state = {
                'entities': current_state.get('entities', {}),
                'packs': current_state.get('packs', {}),
                'species': current_state.get('species', {})
            }

            # Update hashes
            self._entity_hashes = {
                eid: self._hash_entity(data)
                for eid, data in current_state.get('entities', {}).items()
            }
            self._pack_hashes = {
                pid: self._hash_pack(data)
                for pid, data in current_state.get('packs', {}).items()
            }

            return {
                'type': 'full',
                'state': current_state,
                'frame': self._frame_counter,
                'tick': current_state.get('tick', 0)
            }

        # Build delta
        delta = {
            'type': 'delta',
            'frame': self._frame_counter,
            'tick': current_state.get('tick', 0),
            'deltaTime': current_state.get('deltaTime', 0),
            'state': current_state.get('state', 'running'),
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
            'species': current_state.get('species', {})  # Species rarely change
        }

        # Process entities
        current_entities = current_state.get('entities', {})
        current_ids = set(current_entities.keys())
        last_ids = set(self._last_state['entities'].keys())

        # New entities
        for entity_id in current_ids - last_ids:
            delta['entities']['added'][entity_id] = current_entities[entity_id]
            self._entity_hashes[entity_id] = self._hash_entity(current_entities[entity_id])

        # Removed entities
        removed = list(last_ids - current_ids)
        delta['entities']['removed'] = removed
        for entity_id in removed:
            self._entity_hashes.pop(entity_id, None)

        # Modified entities (hash comparison)
        for entity_id in current_ids & last_ids:
            current_data = current_entities[entity_id]
            current_hash = self._hash_entity(current_data)
            last_hash = self._entity_hashes.get(entity_id)

            if current_hash != last_hash:
                delta['entities']['modified'][entity_id] = current_data
                self._entity_hashes[entity_id] = current_hash

        # Process packs
        current_packs = current_state.get('packs', {})
        current_pack_ids = set(current_packs.keys())
        last_pack_ids = set(self._last_state['packs'].keys())

        # New packs
        for pack_id in current_pack_ids - last_pack_ids:
            delta['packs']['added'][pack_id] = current_packs[pack_id]
            self._pack_hashes[pack_id] = self._hash_pack(current_packs[pack_id])

        # Removed packs
        removed_packs = list(last_pack_ids - current_pack_ids)
        delta['packs']['removed'] = removed_packs
        for pack_id in removed_packs:
            self._pack_hashes.pop(pack_id, None)

        # Modified packs (member changes)
        for pack_id in current_pack_ids & last_pack_ids:
            current_pack = current_packs[pack_id]
            current_hash = self._hash_pack(current_pack)
            last_hash = self._pack_hashes.get(pack_id)

            if current_hash != last_hash:
                delta['packs']['modified'][pack_id] = current_pack
                self._pack_hashes[pack_id] = current_hash

        # Update last state
        self._last_state['entities'] = current_entities.copy()
        self._last_state['packs'] = current_packs.copy()
        self._last_state['species'] = current_state.get('species', {}).copy()

        return delta

    def reset(self) -> None:
        """Reset encoder state (useful for reconnections)."""
        self._last_state = {
            'entities': {},
            'packs': {},
            'species': {}
        }
        self._entity_hashes.clear()
        self._pack_hashes.clear()
        self._frame_counter = 0
