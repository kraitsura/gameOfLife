# server/app/simulation/particle_manager.py
import uuid
import random
import math
from typing import Dict, List, Optional

from app.models.simulation import (
    SimulationState, Particle, Species, Position, 
    Velocity, ParticleAttributes, ParticleRules,
    ParticleType, Diet, ReproductionStyle
)
from .group_manager import GroupManager

class ParticleManager:
    def __init__(self, state: SimulationState):
        self.state = state
        self.group_manager = GroupManager(state)

    def add_plant_species(self):
        """Add plant species to simulation"""
        return self.add_species(
            name="Plants",
            color="#00FF00",
            rules=ParticleRules(
                reproductionRate=0,
                energyConsumption=1,  # Added energy consumption for decay
                maxSpeed=0,
                visionRange=0,
                socialDistance=10,
                particleType=ParticleType.PLANT
            ),
            diet=Diet.HERBIVORE,
            reproductionStyle=ReproductionStyle.SELF_REPLICATING,
            initial_count=20
        )

    def add_species(self, name: str, color: str, rules: ParticleRules, 
                   diet: Diet, reproductionStyle: ReproductionStyle,
                   initial_count: int = 10) -> str:
        """Add a new species to the simulation"""
        species_id = str(uuid.uuid4())
        
        self.state.species[species_id] = Species(
            id=species_id,
            name=name,
            color=color,
            baseRules=rules,
            population=initial_count,
            diet=diet,
            reproductionStyle=reproductionStyle
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

        position = Position(
            x=random.uniform(0, self.state.worldWidth),
            y=random.uniform(0, self.state.worldHeight)
        )

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0, species.baseRules.maxSpeed)
        velocity = Velocity(
            x=math.cos(angle) * speed if species.baseRules.particleType != ParticleType.PLANT else 0,
            y=math.sin(angle) * speed if species.baseRules.particleType != ParticleType.PLANT else 0
        )

        # Set initial energy for plants
        initial_energy = 100 if species.baseRules.particleType == ParticleType.PLANT else 50

        particle = Particle(
            id=particle_id,
            position=position,
            velocity=velocity,
            attributes=ParticleAttributes(
                energy=initial_energy,
                diet=species.diet,
                reproductionStyle=species.reproductionStyle,
                packMentality=random.random() if species.baseRules.particleType == ParticleType.CREATURE else 0
            ),
            rules=species.baseRules,
            speciesId=species_id,
            color=species.color
        )

        self.state.particles[particle_id] = particle
        species.population += 1

        return particle_id

    def update_particles(self):
        """Update all particles in the simulation"""
        particles_to_remove = set()
        new_particles = []

        # First update plants (background layer)
        for particle in list(self.state.particles.values()):
            if particle.rules.particleType == ParticleType.PLANT:
                self._update_plant(particle, particles_to_remove)

        # Then update creatures (foreground layer)
        for particle in list(self.state.particles.values()):
            if particle.rules.particleType != ParticleType.PLANT:
                self._update_particle_position(particle)
                self._update_particle_attributes(particle)

                if particle.attributes.energy <= 0 or particle.attributes.hunger >= 150:
                    particles_to_remove.add(particle.id)
                    continue

                nearby = self._get_nearby_particles(particle)
                
                if particle.id not in particles_to_remove:
                    self._apply_behaviors(particle, nearby)
                    self._handle_eating(particle, nearby)

                    if self._should_reproduce(particle):
                        new_particle = self._reproduce(particle)
                        if new_particle:
                            new_particles.append(new_particle)

        # Process removals and additions
        for particle_id in particles_to_remove:
            self._remove_particle(particle_id)

        for new_particle in new_particles:
            self.state.particles[new_particle.id] = new_particle
            self.state.species[new_particle.speciesId].population += 1

    def _update_plant(self, plant: Particle, particles_to_remove: set):
        """Update plant particle"""
        # Gradual energy decay
        decay_rate = plant.rules.energyConsumption
        plant.attributes.energy -= decay_rate

        # Update color based on energy level
        energy_percentage = plant.attributes.energy / 100
        # Convert hex to RGB, then adjust based on energy
        r = int(0)  # Keep red at 0
        g = int(255 * energy_percentage)  # Reduce green based on energy
        b = int(0)  # Keep blue at 0
        plant.color = f"#{r:02x}{g:02x}{b:02x}"

        # Remove dead plants
        if plant.attributes.energy <= 0:
            particles_to_remove.add(plant.id)

    def _update_particle_position(self, particle: Particle):
        """Update particle position"""
        particle.position.x = (particle.position.x + particle.velocity.x) % self.state.worldWidth
        particle.position.y = (particle.position.y + particle.velocity.y) % self.state.worldHeight

    def _update_particle_attributes(self, particle: Particle):
        """Update particle attributes"""
        particle.attributes.age += 1
        speed = math.sqrt(particle.velocity.x**2 + particle.velocity.y**2)
        energy_cost = particle.rules.energyConsumption * (speed / particle.rules.maxSpeed)
        particle.attributes.energy -= energy_cost * 0.5
        particle.attributes.hunger += 0.05

        if speed < 0.1:
            particle.attributes.energy = min(100, particle.attributes.energy + 0.02)

        if particle.attributes.energy > 90 and particle.attributes.hunger > 90:
            particle.attributes.highEnergyHungerTime += 1
        else:
            particle.attributes.highEnergyHungerTime = 0

    def _get_nearby_particles(self, particle: Particle) -> List[Particle]:
        """Get particles within vision range, filtered by diet and hunger rules"""
        nearby = []
        for other in self.state.particles.values():
            if other.id == particle.id:
                continue

            # Carnivores completely ignore plants
            if (particle.attributes.diet == Diet.CARNIVORE and 
                other.rules.particleType == ParticleType.PLANT):
                continue

            # Herbivores and omnivores only see plants when hungry
            if (other.rules.particleType == ParticleType.PLANT and 
                particle.attributes.diet in [Diet.HERBIVORE, Diet.OMNIVORE] and 
                particle.attributes.hunger >= 50):
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

        # Filter nearby particles to only include same species
        same_species = [p for p in nearby if p.speciesId == particle.speciesId]
        if not same_species:
            return

        separation = self._calculate_separation(particle, nearby)  # Keep separation for all particles to avoid collisions
        cohesion = self._calculate_cohesion(particle, same_species)  # Only cohese with same species
        alignment = self._calculate_alignment(particle, same_species)  # Only align with same species

        particle.velocity.x += (separation[0] + cohesion[0] + alignment[0]) * 0.1
        particle.velocity.y += (separation[1] + cohesion[1] + alignment[1]) * 0.1

        speed = math.sqrt(particle.velocity.x**2 + particle.velocity.y**2)
        if speed > particle.rules.maxSpeed:
            particle.velocity.x = (particle.velocity.x / speed) * particle.rules.maxSpeed
            particle.velocity.y = (particle.velocity.y / speed) * particle.rules.maxSpeed

    def _calculate_cohesion(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate cohesion force only with same species"""
        if not nearby:
            return (0, 0)

        center_x = sum(p.position.x for p in nearby) / len(nearby)
        center_y = sum(p.position.y for p in nearby) / len(nearby)

        return (center_x - particle.position.x, center_y - particle.position.y)

    def _calculate_alignment(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate alignment force only with same species"""
        if not nearby:
            return (0, 0)

        avg_vx = sum(p.velocity.x for p in nearby) / len(nearby)
        avg_vy = sum(p.velocity.y for p in nearby) / len(nearby)

        return (avg_vx - particle.velocity.x, avg_vy - particle.velocity.y)

    def _calculate_separation(self, particle: Particle, nearby: List[Particle]) -> tuple[float, float]:
        """Calculate separation force from all particles to avoid collisions"""
        if not nearby:
            return (0, 0)

        force_x = force_y = 0
        for other in nearby:
            dx = particle.position.x - other.position.x
            dy = particle.position.y - other.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Stronger separation force for different species
            separation_multiplier = 1.0 if other.speciesId == particle.speciesId else 2.0

            if distance < particle.rules.socialDistance:
                force_x += (dx / distance if distance > 0 else random.random() - 0.5) * separation_multiplier
                force_y += (dy / distance if distance > 0 else random.random() - 0.5) * separation_multiplier

        return (force_x, force_y)

    def _should_reproduce(self, particle: Particle) -> bool:
        """Determine if particle should reproduce"""
        if particle.attributes.reproductionStyle == ReproductionStyle.SELF_REPLICATING:
            return (particle.attributes.energy > 90 and 
                   particle.attributes.hunger > 90 and
                   particle.attributes.highEnergyHungerTime > 50)
        else:
            nearby = self._get_nearby_particles(particle)
            potential_mates = [
                p for p in nearby 
                if (p.speciesId == particle.speciesId and
                    p.attributes.energy > 90 and
                    p.attributes.hunger > 90)
            ]
            
            for mate in potential_mates:
                meeting_count = particle.attributes.meetingCount.get(mate.id, 0)
                if meeting_count >= 2:
                    return True
                
                particle.attributes.meetingCount[mate.id] = meeting_count + 1
                mate.attributes.meetingCount[particle.id] = (
                    mate.attributes.meetingCount.get(particle.id, 0) + 1
                )
            
            return False

    def _reproduce(self, parent: Particle) -> Optional[Particle]:
        """Create a new particle through reproduction"""
        if parent.attributes.reproductionStyle == ReproductionStyle.TWO_PARENTS:
            nearby = self._get_nearby_particles(parent)
            mates = [
                p for p in nearby 
                if (p.speciesId == parent.speciesId and
                    p.attributes.energy > 90 and
                    p.attributes.hunger > 90 and
                    parent.attributes.meetingCount.get(p.id, 0) >= 2)
            ]
            
            if not mates:
                return None
                
            mate = random.choice(mates)
            child = self._create_child_particle(parent, mate)
            self.group_manager.create_group([parent, mate, child], 
                             parent_ids={parent.id, mate.id},
                             child_id=child.id)
            return child
        else:
            return self._create_child_particle(parent)


    def _create_child_particle(self, parent: Particle, mate: Optional[Particle] = None) -> Particle:
        """Create a new particle through reproduction"""
        particle_id = str(uuid.uuid4())

        angle = random.uniform(0, 2 * math.pi)
        distance = parent.rules.socialDistance
        position = Position(
            x=(parent.position.x + math.cos(angle) * distance) % self.state.worldWidth,
            y=(parent.position.y + math.sin(angle) * distance) % self.state.worldHeight
        )

        velocity = Velocity(
            x=random.uniform(-1, 1) * parent.rules.maxSpeed,
            y=random.uniform(-1, 1) * parent.rules.maxSpeed
        )

        if mate:
            initial_energy = (parent.attributes.energy + mate.attributes.energy) * 0.25
            parent.attributes.energy *= 0.5
            mate.attributes.energy *= 0.5
            pack_mentality = (parent.attributes.packMentality + mate.attributes.packMentality) / 2
        else:
            initial_energy = parent.attributes.energy * 0.5
            parent.attributes.energy *= 0.5
            pack_mentality = parent.attributes.packMentality

        parent.attributes.lastReproduced = 0
        
        # Add mutation to pack mentality
        pack_mentality += random.uniform(-0.1, 0.1)
        pack_mentality = max(0, min(1, pack_mentality))

        return Particle(
            id=particle_id,
            position=position,
            velocity=velocity,
            attributes=ParticleAttributes(
                energy=initial_energy,
                diet=parent.attributes.diet,
                reproductionStyle=parent.attributes.reproductionStyle,
                packMentality=pack_mentality,
                isChild=True
            ),
            rules=parent.rules,
            speciesId=parent.speciesId,
            color=parent.color
        )

    def _remove_particle(self, particle_id: str):
        """Remove a particle from the simulation"""
        if particle_id in self.state.particles:
            particle = self.state.particles[particle_id]
            
            # Remove from species population count
            if particle.speciesId in self.state.species:
                self.state.species[particle.speciesId].population -= 1
            
            # Remove from group if in one
            if particle.attributes.groupId:
                self._leave_group(particle, particle.attributes.groupId)
            
            # Remove from simulation
            del self.state.particles[particle_id]
            
            # Clean up meeting counts in other particles
            for other_particle in self.state.particles.values():
                if particle_id in other_particle.attributes.meetingCount:
                    del other_particle.attributes.meetingCount[particle_id]

    def _can_eat(self, predator: Particle, prey: Particle) -> bool:
        """Determine if predator can eat prey"""
        # Can't eat your own species
        if predator.speciesId == prey.speciesId:
            return False

        # Relaxed energy/hunger requirements
        if predator.attributes.energy > 90:  # Don't eat if nearly full
            return False

        # Need more energy and hunger than prey to eat it
        if (predator.attributes.energy <= prey.attributes.energy or
            predator.attributes.hunger <= prey.attributes.hunger):
            return False

        # Plants can be eaten by herbivores and omnivores
        if prey.rules.particleType == ParticleType.PLANT:
            return predator.attributes.diet in [Diet.HERBIVORE, Diet.OMNIVORE]
        
        # Get prey's species to check diet type
        if prey.speciesId not in self.state.species:
            return False
        prey_species = self.state.species[prey.speciesId]

        # Diet-based rules
        if predator.attributes.diet == Diet.HERBIVORE:
            # Herbivores can't eat other creatures
            return False
        elif predator.attributes.diet == Diet.CARNIVORE:
            # Carnivores can only eat herbivores
            return prey_species.diet == Diet.HERBIVORE
        else:  # OMNIVORE
            # Omnivores can eat everything except their own species (checked above)
            return True

    def _handle_eating(self, particle: Particle, nearby: List[Particle]):
        """Handle particle eating behavior"""
        if not nearby:
            return

        # Calculate distances and store in tuples
        nearby_with_distance = []
        for other in nearby:
            dx = particle.position.x - other.position.x
            dy = particle.position.y - other.position.y
            distance = math.sqrt(dx * dx + dy * dy)
            nearby_with_distance.append((distance, other))
        
        # Sort by the distance (first element of tuple)
        nearby_with_distance.sort(key=lambda x: x[0])

        for distance, other in nearby_with_distance:
            if not self._can_eat(particle, other):
                continue

            if distance <= particle.attributes.size * 2 + other.attributes.size:
                # Transfer energy from prey to predator
                if other.rules.particleType == ParticleType.PLANT:
                    energy_gain = 30  # Fixed energy gain from plants
                else:
                    energy_gain = other.attributes.energy * 0.7  # Increased energy transfer

                particle.attributes.energy = min(100, particle.attributes.energy + energy_gain)
                particle.attributes.hunger = max(0, particle.attributes.hunger - energy_gain)
                particle.attributes.lastAte = 0

                # Remove eaten particle
                self._remove_particle(other.id)
                break