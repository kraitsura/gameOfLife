# server/app/simulation/simulation_manager.py
import asyncio
from typing import Dict, Optional
import random

from app.models.simulation import (
    SimulationState, ParticleRules, Diet, 
    ReproductionStyle, ParticleType
)
from .particle_manager import ParticleManager
from .group_manager import GroupManager

class SimulationManager:
    def __init__(self, world_width: int = 800, world_height: int = 600):
        self.state = SimulationState(
            particles={},
            species={},
            groups={},
            worldWidth=world_width,
            worldHeight=world_height,
            tickCount=0
        )
        self.particle_manager = ParticleManager(self.state)
        self.group_manager = GroupManager(self.state)
        self.is_running: bool = False
        self.tick_rate: float = 1/60  # 60 FPS
        self.plant_spawn_rate: float = 0.1
        self._simulation_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the simulation loop"""
        if not self.is_running:
            self.is_running = True
            self._simulation_task = asyncio.create_task(self._simulation_loop())

    async def pause(self):
        """Pause the simulation"""
        self.is_running = False
        if self._simulation_task:
            try:
                self._simulation_task.cancel()
                await self._simulation_task
            except asyncio.CancelledError:
                pass
            self._simulation_task = None

    def get_state(self) -> Dict:
        """Get current simulation state"""
        state_dict = self.state.dict()
        
        # Convert sets to lists in groups
        for group in state_dict['groups'].values():
            if 'memberIds' in group:
                group['memberIds'] = list(group['memberIds'])
            if 'parentIds' in group and group['parentIds'] is not None:
                group['parentIds'] = list(group['parentIds'])
        
        return state_dict

    def add_plant_species(self):
        """Add plant species to simulation"""
        return self.particle_manager.add_plant_species()

    def add_species(self, name: str, color: str, rules: ParticleRules, 
                   diet: Diet, reproductionStyle: ReproductionStyle,
                   initial_count: int = 10) -> str:
        """Add a new species to the simulation"""
        return self.particle_manager.add_species(
            name, color, rules, diet, reproductionStyle, initial_count
        )

    async def _simulation_loop(self):
        """Main simulation loop"""
        while self.is_running:
            start_time = asyncio.get_event_loop().time()

            try:
                # Spawn plants randomly
                if random.random() < self.plant_spawn_rate:
                    plant_species_id = next(
                        (s.id for s in self.state.species.values() 
                         if s.baseRules.particleType == ParticleType.PLANT),
                        None
                    )
                    if plant_species_id:
                        self.particle_manager.add_particle(plant_species_id)

                # Update simulation state
                self.particle_manager.update_particles()
                self.group_manager.update_groups()
                self.state.tickCount += 1

                # Control loop timing
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < self.tick_rate:
                    await asyncio.sleep(self.tick_rate - elapsed)
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                self.is_running = False
                break