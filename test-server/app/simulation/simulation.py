# simulation.py
import logging
import time
import asyncio
from typing import Set, Any
from app.simulation.core.context import SimulationContext
from app.simulation.models import Entity, Species, Pack
from app.simulation.core import EntityType, Trait

class SimulationManager:
    def __init__(self, world_width: int, world_height: int):
        """Initialize the simulation with a world of given dimensions."""
        self.world = SimulationContext(world_width, world_height)
        self._is_running: bool = False
        self.connections: Set[Any] = set()  # Add missing connections set
        logging.basicConfig(level=logging.INFO)
        logging.info("SimulationManager initialized with world size (%d, %d)", world_width, world_height)
        self.fixed_dt = 0.016  # Fixed time step
        self.accumulator = 0.0
        self.last_update_time = time.time()
        self._update_task = None  # Store the update task

    @property
    def is_running(self) -> bool:
        """Thread-safe access to running state."""
        return self._is_running

    async def start(self) -> None:
        """Start the simulation asynchronously."""
        if self.is_running:
            logging.info("Simulation already running.")
            return

        logging.info("Simulation started.")
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
                self.world.update(self.fixed_dt)
                self.accumulator -= self.fixed_dt

            # Allow other tasks to run
            await asyncio.sleep(0.01)

    async def pause(self) -> None:
        """Pause the simulation."""
        logging.info("Simulation paused.")
        self._is_running = False
        if self._update_task:
            await self._update_task

    def add_species(self, name: str, color: str, entity_type: EntityType, base_traits: Set[Trait], initial_count: int) -> None:
        """Add a species to the world."""
        try:
            # Validate inputs
            if not name or not isinstance(initial_count, int) or initial_count <= 0:
                raise ValueError("Invalid species parameters")
            
            species = Species(name, color, entity_type, base_traits, initial_count)
            self.world.register(species)

            logging.info("Species '%s' added with initial count %d.", name, initial_count)
        except Exception as e:
            logging.error("Failed to add species '%s': %s", name, str(e))
            raise

    def get_state(self) -> dict:
        """Return the current state of the simulation."""
        try:
            return {
                "entities": {str(id): entity.serialize() 
                            for id, entity in self.world._objects.items() if isinstance(entity, Entity)},
                "species": {str(id): species.serialize() 
                          for id, species in self.world._objects.items() if isinstance(species, Species)},
                "packs": {str(id): pack.serialize() 
                         for id, pack in self.world._objects.items() if isinstance(pack, Pack)},
                "worldWidth": self.world.width,
                "worldHeight": self.world.height,
                "tickCount": self.world.tick_rate,
                "isRunning": self._is_running
            }
        except Exception as e:
            logging.error("Error getting simulation state: %s", str(e))
            return {"error": "Failed to get simulation state"}

