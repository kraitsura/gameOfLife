from app.simulation.core import Component, VITALITY_CONFIG
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class VitalityComponent(Component):
    """
    Manages entity health, energy, and survival.

    Energy decreases over time through metabolism and movement.
    Hunger increases when energy is low.
    Health decreases when starving or exhausted.
    Entity dies when health reaches 0.
    """

    def __init__(
        self,
        max_energy: float = VITALITY_CONFIG["BASE_ENERGY"],
        max_health: float = 100.0
    ):
        self.max_energy = max_energy
        self.max_health = max_health
        self.current_energy = max_energy
        self.current_health = max_health
        self.hunger = 0.0
        self.age = 0.0
        self.last_ate = 0.0

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """
        Update vitality stats each frame.

        1. Increase age
        2. Decrease energy (metabolism + movement cost)
        3. Increase hunger when low energy
        4. Decrease health when starving/exhausted
        5. Die when health reaches 0
        """
        from app.simulation.models.entity import EntityState

        # Don't update if already dead (prevents duplicate death logging)
        if owner.state == EntityState.DEAD:
            return

        self.age += dt
        self.last_ate += dt

        # Energy decay from metabolism
        energy_cost = VITALITY_CONFIG["ENERGY_DECAY_RATE"] * dt

        # Additional energy cost based on movement speed
        physics = owner.get_component('PhysicsComponent')
        if physics:
            speed = physics.velocity.magnitude()
            movement_cost = speed * 0.01 * dt  # Scale with speed
            energy_cost += movement_cost

        self.current_energy -= energy_cost

        # Hunger increases when energy is low
        if self.current_energy < self.max_energy * 0.5:
            self.hunger += VITALITY_CONFIG["HUNGER_RATE"] * dt

        # Health effects from starvation
        if self.hunger > 75:
            self.current_health -= 0.5 * dt
            logging.debug(f"Entity {owner.id} is starving (hunger: {self.hunger:.1f})")

        # Health effects from energy depletion
        if self.current_energy <= 0:
            self.current_health -= 1.0 * dt
            logging.debug(f"Entity {owner.id} is exhausted (energy: {self.current_energy:.1f})")

        # Cap values
        self.current_energy = max(0, min(self.max_energy, self.current_energy))
        self.hunger = max(0, min(100, self.hunger))
        self.current_health = max(0, min(self.max_health, self.current_health))

        # Sync with entity stats
        owner.stats.current_energy = self.current_energy
        owner.stats.current_health = self.current_health
        owner.stats.max_energy = self.max_energy
        owner.stats.max_health = self.max_health

        # Die when health depleted (only log once)
        if self.current_health <= 0:
            logging.info(f"Entity {owner.id} died from health depletion")
            owner.kill()

    def restore_energy(self, amount: float) -> float:
        """
        Restore energy (e.g., from eating food).

        Args:
            amount: Amount of energy to restore

        Returns:
            Actual amount restored (capped at max_energy)
        """
        old_energy = self.current_energy
        self.current_energy = min(self.max_energy, self.current_energy + amount)
        restored = self.current_energy - old_energy

        # Reduce hunger when eating
        self.hunger = max(0, self.hunger - (restored * 0.5))
        self.last_ate = 0.0

        return restored
