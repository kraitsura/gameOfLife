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

        # Configure logging to INFO level for better visibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.info("SimulationManager initialized with world size (%d, %d)", world_width, world_height)
        self.fixed_dt = 0.016  # Fixed time step
        self.accumulator = 0.0
        self.last_update_time = time.time()
        self._update_task = None  # Store the update task
        self.plant_species_id: str | None = None  # Track plant species for spawning
        self.plant_spawn_rate: float = 0.05  # 5% chance per tick = ~3 spawn attempts/sec instead of 6

    @property
    def is_running(self) -> bool:
        """Thread-safe access to running state."""
        return self._is_running

    async def start(self) -> None:
        """Start the simulation asynchronously."""
        if self.is_running:
            logging.info("Simulation already running, ignoring start request.")
            return

        logging.info("Starting simulation...")
        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logging.info("Simulation started successfully. Update task created.")

    async def _update_loop(self) -> None:
        """Main update loop running asynchronously."""
        logging.info("Update loop started")

        try:
            while self._is_running:
                try:
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

                except asyncio.CancelledError:
                    # Task was cancelled (normal during pause/shutdown)
                    logging.info("Update loop cancelled")
                    raise  # Re-raise to properly handle cancellation

                except Exception as e:
                    # Log the error but continue the simulation
                    logging.error(
                        "Error in simulation update loop: %s",
                        str(e),
                        exc_info=True  # Include full stack trace
                    )
                    # Continue running despite the error
                    await asyncio.sleep(0.1)  # Brief pause before retrying

        except asyncio.CancelledError:
            logging.info("Update loop task cancelled gracefully")
        finally:
            logging.info("Update loop stopped")

    async def pause(self) -> None:
        """Pause the simulation."""
        if not self.is_running:
            logging.info("Simulation already paused, ignoring pause request.")
            return

        logging.info("Pausing simulation...")
        self._is_running = False

        if self._update_task and not self._update_task.done():
            # Cancel the task instead of waiting for it to complete
            # This prevents deadlock when the task is stuck
            self._update_task.cancel()

            try:
                # Wait briefly for cancellation to complete
                await asyncio.wait_for(self._update_task, timeout=2.0)
            except asyncio.CancelledError:
                logging.info("Update task cancelled successfully")
            except asyncio.TimeoutError:
                logging.warning("Update task cancellation timed out - task may be stuck")
            except Exception as e:
                logging.error("Error during task cancellation: %s", str(e), exc_info=True)

        logging.info("Simulation paused successfully")

    def _spawn_random_plant(self) -> None:
        """Spawn plants based on local density (carrying capacity)."""
        if not self.plant_species_id:
            return

        plant_species = self.world.get_by_id(Species, self.plant_species_id)
        if not plant_species:
            logging.warning("Plant species not found for spawning")
            return

        # Random position candidate
        position = Vector2D(
            random.uniform(0, self.world.width),
            random.uniform(0, self.world.height)
        )

        # Check local plant density (carrying capacity)
        local_radius = 30.0
        max_plants_in_radius = 5

        nearby_entities = self.world.query_nearby_entities(position, local_radius)
        plant_count = sum(
            1 for e in nearby_entities
            if hasattr(e, 'species_id') and e.species_id == self.plant_species_id
        )

        # Don't spawn if area is at carrying capacity
        if plant_count >= max_plants_in_radius:
            return

        # Spawn plant
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

