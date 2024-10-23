# server/app/simulation/simulation_manager.py
import asyncio
import uuid
import random
import math
from typing import Dict, List, Optional
import numpy as np

from app.models.simulation import (
    SimulationState, Particle, Species, Position, 
    Velocity, ParticleAttributes, ParticleRules
)

class SimulationManager:
    def __init__(self, world_width: int = 800, world_height: int = 600):
        self.state = SimulationState(
            particles={},
            species={},
            worldWidth=world_width,
            worldHeight=world_height,
            tickCount=0
        )
        self.is_running: bool = False
        self.tick_rate: float = 1/60  # 60 FPS

    def get_state(self) -> Dict:
        """Get current simulation state"""
        return self.state.dict()

    async def start(self):
        """Start the simulation loop"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._simulation_loop())

    async def pause(self):
        """Pause the simulation"""
        self.is_running = False

    def add_species(self, name: str, color: str, rules: ParticleRules, initial_count: int = 10) -> str:
        """Add a new species to the simulation"""
        species_id = str(uuid.uuid4())
        
        self.state.species[species_id] = Species(
            id=species_id,
            name=name,
            color=color,
            baseRules=rules,
            population=initial_count
        )

        # Create initial particles for the species
        for _ in range(initial_count):
            self.add_particle(species_id)

        return species_id

    def add_particle(self, species_id: str) -> str:
        """Add a new particle to the simulation"""
        if species_id not in self.state.species:
            raise ValueError("Species not found")

        species = self.state.species[species_id]
        particle_id = str(uuid.uuid4())

        # Random position within world bounds
        position = Position(
            x=random.uniform(0, self.state.worldWidth),
            y=random.uniform(0, self.state.worldHeight)
        )

        # Random initial velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0, species.baseRules.maxSpeed)
        velocity = Velocity(
            x=math.cos(angle) * speed,
            y=math.sin(angle) * speed
        )

        particle = Particle(
            id=particle_id,
            position=position,
            velocity=velocity,
            attributes=ParticleAttributes(),
            rules=species.baseRules,
            speciesId=species_id,
            color=species.color
        )

        self.state.particles[particle_id] = particle
        species.population += 1

        return particle_id

    async def _simulation_loop(self):
        """Main simulation loop"""
        while self.is_running:
            start_time = asyncio.get_event_loop().time()

            try:
                # Update simulation state
                self._update_particles()
                self.state.tickCount += 1

                # Control loop timing
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed < self.tick_rate:
                    await asyncio.sleep(self.tick_rate - elapsed)
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                self.is_running = False
                break

    def _update_particles(self):
        """Update all particles in the simulation"""
        particles_to_remove = set()
        new_particles = []

        for particle in self.state.particles.values():
            # Update position
            particle.position.x += particle.velocity.x
            particle.position.y += particle.velocity.y

            # Wrap around world boundaries
            particle.position.x %= self.state.worldWidth
            particle.position.y %= self.state.worldHeight

            # Update attributes
            particle.attributes.age += 1
            particle.attributes.energy -= particle.rules.energyConsumption
            particle.attributes.hunger += 1

            # Get nearby particles
            nearby = self.get_nearby_particles(particle)
            
            # Apply behaviors
            self._apply_behaviors(particle, nearby)

            # Handle reproduction
            if self._should_reproduce(particle):
                new_particles.append(self._reproduce(particle))

            # Handle death
            if particle.attributes.energy <= 0:
                particles_to_remove.add(particle.id)

        # Remove dead particles
        for particle_id in particles_to_remove:
            self._remove_particle(particle_id)

        # Add new particles
        for new_particle in new_particles:
            self.state.particles[new_particle.id] = new_particle
            self.state.species[new_particle.speciesId].population += 1

    def get_nearby_particles(self, particle: Particle) -> List[Particle]:
        """Get particles within vision range"""
        nearby = []
        for other in self.state.particles.values():
            if other.id == particle.id:
                continue

            dx = particle.position.x - other.position.x
            dy = particle.position.y - other.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= particle.rules.visionRange:
                nearby.append(other)

        return nearby

    def _apply_behaviors(self, particle: Particle, nearby: List[Particle]):
        """Apply particle behaviors based on nearby particles"""
        if not nearby:
            return

        # Calculate steering forces
        separation = self._calculate_separation(particle, nearby)
        cohesion = self._calculate_cohesion(particle, nearby)
        alignment = self._calculate_alignment(particle, nearby)

        # Apply forces to velocity
        particle.velocity.x += (separation[0] + cohesion[0] + alignment[0]) * 0.1
        particle.velocity.y += (separation[1] + cohesion[1] + alignment[1]) * 0.1

        # Limit speed
        speed = math.sqrt(particle.velocity.x**2 + particle.velocity.y**2)
        if speed > particle.rules.maxSpeed:
            particle.velocity.x = (particle.velocity.x / speed) * particle.rules.maxSpeed
            particle.velocity.y = (particle.velocity.y / speed) * particle.rules.maxSpeed

    def _calculate_separation(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate separation force"""
        if not nearby:
            return (0, 0)

        force_x = force_y = 0
        for other in nearby:
            dx = particle.position.x - other.position.x
            dy = particle.position.y - other.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < particle.rules.socialDistance:
                force_x += dx / distance
                force_y += dy / distance

        return (force_x, force_y)

    def _calculate_cohesion(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate cohesion force"""
        same_species = [p for p in nearby if p.speciesId == particle.speciesId]
        if not same_species:
            return (0, 0)

        center_x = sum(p.position.x for p in same_species) / len(same_species)
        center_y = sum(p.position.y for p in same_species) / len(same_species)

        return (center_x - particle.position.x, center_y - particle.position.y)

    def _calculate_alignment(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate alignment force"""
        same_species = [p for p in nearby if p.speciesId == particle.speciesId]
        if not same_species:
            return (0, 0)

        avg_vx = sum(p.velocity.x for p in same_species) / len(same_species)
        avg_vy = sum(p.velocity.y for p in same_species) / len(same_species)

        return (avg_vx - particle.velocity.x, avg_vy - particle.velocity.y)

    def _should_reproduce(self, particle: Particle) -> bool:
        """Determine if particle should reproduce"""
        if (particle.attributes.energy > 50 and
            particle.attributes.age > 100 and
            particle.attributes.lastReproduced > 200 and
            random.random() < particle.rules.reproductionRate):
            return True
        return False

    def _reproduce(self, parent: Particle) -> Particle:
        """Create a new particle through reproduction"""
        particle_id = str(uuid.uuid4())

        # Position near parent
        angle = random.uniform(0, 2 * math.pi)
        distance = parent.rules.socialDistance
        position = Position(
            x=(parent.position.x + math.cos(angle) * distance) % self.state.worldWidth,
            y=(parent.position.y + math.sin(angle) * distance) % self.state.worldHeight
        )

        # Random initial velocity
        velocity = Velocity(
            x=random.uniform(-1, 1) * parent.rules.maxSpeed,
            y=random.uniform(-1, 1) * parent.rules.maxSpeed
        )

        # Split energy with parent
        parent.attributes.energy *= 0.5
        parent.attributes.lastReproduced = 0

        return Particle(
            id=particle_id,
            position=position,
            velocity=velocity,
            attributes=ParticleAttributes(energy=parent.attributes.energy),
            rules=parent.rules,
            speciesId=parent.speciesId,
            color=parent.color
        )

    def _remove_particle(self, particle_id: str):
        """Remove a particle from the simulation"""
        if particle_id in self.state.particles:
            particle = self.state.particles[particle_id]
            self.state.species[particle.speciesId].population -= 1
            del self.state.particles[particle_id]