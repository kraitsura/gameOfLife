# simulation.py
import logging
import time
import asyncio
import random
from typing import Set, Any
from app.simulation.core.context import SimulationContext
from app.simulation.models import Entity, Species, Pack
from app.simulation.core import EntityType, Trait
from app.simulation.core.vector import Vector2D

class SimulationManager:
    def __init__(self, world_width: int, world_height: int):
        """Initialize the simulation with a world of given dimensions."""
        self.world = SimulationContext(world_width, world_height)
        self._is_running: bool = False
        self.connections: Set[Any] = set()  # Add missing connections set
        logging.basicConfig(level=logging.WARNING)
        logging.debug("SimulationManager initialized with world size (%d, %d)", world_width, world_height)
        self.fixed_dt = 0.016  # Fixed time step
        self.accumulator = 0.0
        self.last_update_time = time.time()
        self._update_task = None  # Store the update task
        self.plant_species_id: str | None = None  # Track plant species for spawning
        self.plant_spawn_rate: float = 0.1  # 10% chance per tick to spawn a plant

    @property
    def is_running(self) -> bool:
        """Thread-safe access to running state."""
        return self._is_running

    async def start(self) -> None:
        """Start the simulation asynchronously."""
        if self.is_running:
            logging.debug("Simulation already running.")
            return

        logging.debug("Simulation started.")
        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())

    async def _update_loop(self) -> None:
        """Main update loop running asynchronously."""
        while self._is_running:
            current_time = time.time()
            frame_time = current_time - self.last_update_time
            self.last_update_time = current_time

            self.accumulator += frame_time

            while self.accumulator >= self.fixed_dt:
                # Spawn random plants each tick (10% chance)
                if self.plant_species_id and random.random() < self.plant_spawn_rate:
                    self._spawn_random_plant()

                self.world.update(self.fixed_dt)

                # Clean up any out-of-bounds entities
                self._cleanup_out_of_bounds_entities()

                self.accumulator -= self.fixed_dt

            # Allow other tasks to run
            await asyncio.sleep(0.01)

    async def pause(self) -> None:
        """Pause the simulation."""
        logging.debug("Simulation paused.")
        self._is_running = False
        if self._update_task:
            await self._update_task

    def _spawn_random_plant(self) -> None:
        """Spawn a random plant at a random position."""
        if not self.plant_species_id:
            return

        plant_species = self.world.get_by_id(Species, self.plant_species_id)
        if not plant_species:
            logging.warning("Plant species not found for spawning")
            return

        # Random position in world
        position = Vector2D(
            random.uniform(0, self.world.width),
            random.uniform(0, self.world.height)
        )

        # Create and register plant entity
        plant = plant_species.create_entity(position)
        self.world.register(plant)

    def add_species(self, name: str, color: str, entity_type: EntityType, base_traits: Set[Trait], initial_count: int) -> None:
        """Add a species to the world."""
        try:
            # Validate inputs
            if not name or not isinstance(initial_count, int) or initial_count <= 0:
                raise ValueError("Invalid species parameters")

            species = Species(name, entity_type, color, base_traits, initial_count)
            self.world.register(species)

            # Track plant species for random spawning
            if entity_type == EntityType.PLANT:
                self.plant_species_id = species.id

            # Spawn initial entities at random positions
            for _ in range(initial_count):
                position = Vector2D(
                    random.uniform(0, self.world.width),
                    random.uniform(0, self.world.height)
                )
                entity = species.create_entity(position)
                self.world.register(entity)

            logging.debug("Species '%s' added with initial count %d entities spawned.", name, initial_count)
        except Exception as e:
            logging.error("Failed to add species '%s': %s", name, str(e))
            raise

    def get_state(self) -> dict:
        """Return the current state of the simulation."""
        try:
            # Get objects by type using the context's type-safe methods
            entities = self.world.get_objects_by_type(Entity)
            species = self.world.get_objects_by_type(Species)
            packs = self.world.get_objects_by_type(Pack)

            # It's OK to have no entities (they might all be dead temporarily)
            # But we should always have species defined
            if not species:
                logging.warning("No species found in simulation - this should not happen")

            return {
                "entities": {str(entity.id): entity.serialize() for entity in entities},
                "species": {str(sp.id): sp.serialize() for sp in species},
                "packs": {str(pack.id): pack.serialize() for pack in packs} if packs else {},
                "worldWidth": self.world.width,
                "worldHeight": self.world.height,
                "tickRate": self.world.tick_rate,
                "isRunning": self._is_running
            }
        except Exception as e:
            logging.error("Error getting simulation state: %s", str(e))
            return {"error": f"Failed to get simulation state: {str(e)}"}

    def _cleanup_out_of_bounds_entities(self) -> None:
        """
        Remove entities that have escaped world boundaries.

        This is a safety mechanism to prevent particles from wandering outside
        the simulation space. Any entity with position outside [0, width] or [0, height]
        will be removed from the simulation.
        """
        entities = self.world.get_objects_by_type(Entity)
        removed_count = 0

        for entity in entities:
            # Check if entity is out of bounds
            if (entity.position.x < 0 or entity.position.x > self.world.width or
                entity.position.y < 0 or entity.position.y > self.world.height):

                logging.warning(
                    f"Removing out-of-bounds entity {entity.id} ({entity.type.value}) "
                    f"at position ({entity.position.x:.1f}, {entity.position.y:.1f}). "
                    f"World bounds: (0, 0) to ({self.world.width}, {self.world.height})"
                )

                # Kill the entity to trigger cleanup
                entity.kill()
                removed_count += 1

        if removed_count > 0:
            logging.info(f"Cleaned up {removed_count} out-of-bounds entities")

