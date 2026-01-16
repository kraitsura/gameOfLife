# Phase 0: Critical System Fixes - Implementation Plan

**Version:** 1.0
**Date:** 2025-10-18
**Status:** Planning Phase
**Priority:** CRITICAL

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current System Problems](#current-system-problems)
3. [Fix 1: Re-enable Energy and Hunger System](#fix-1-re-enable-energy-and-hunger-system)
4. [Fix 2: Differentiate Species Stats](#fix-2-differentiate-species-stats)
5. [Fix 3: Implement Basic Reproduction](#fix-3-implement-basic-reproduction)
6. [Fix 4: Fix Plant Spawning](#fix-4-fix-plant-spawning)
7. [Fix 5: Balance Energy Economy](#fix-5-balance-energy-economy)
8. [Fix 6: Add Flee Behavior](#fix-6-add-flee-behavior)
9. [Testing Strategy](#testing-strategy)
10. [Success Criteria](#success-criteria)

---

## Executive Summary

### Purpose
This document outlines critical bug fixes required to make the multi-species particle simulation functional. Currently, the simulation has several **blocking issues** that prevent it from exhibiting realistic ecosystem dynamics, emergent behavior, and long-term stability.

### Goals
1. **Enable survival mechanics**: Creatures must need to eat to survive (currently disabled)
2. **Create species differentiation**: Different species should have different capabilities
3. **Prevent extinction**: Implement reproduction so populations can grow
4. **Balance resources**: Plants should respawn at sustainable rates
5. **Add realistic behavior**: Prey should flee from predators

### Timeline
**Estimated Time:** 2-3 days for all 6 fixes

### Impact
These fixes will transform the simulation from a broken tech demo into a functioning ecosystem where:
- Predator-prey dynamics emerge naturally
- Population cycles occur (boom and bust)
- Species compete for resources
- Behaviors are meaningful (hunting, fleeing, reproducing)
- Simulations can run for 30+ minutes without total extinction

---

## Current System Problems

### Critical Issues Identified

Based on comprehensive code analysis, the simulation has these **blocking bugs**:

#### 1. ⚠️ Energy and Hunger System is DISABLED
**Location:** `server/app/simulation/core/config.py:24-25`
```python
VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.0,  # DISABLED - should be > 0
    "HUNGER_RATE": 0.0,        # DISABLED - should be > 0
    "REPRODUCTION_THRESHOLD": 90.0
}
```
**Problem:** Creatures never need to eat. They wander aimlessly with no survival pressure.
**Impact:** No predator-prey dynamics, no resource competition, no meaningful behavior.

#### 2. ⚠️ All Species Have Identical Stats
**Location:** `server/app/simulation/models/entity.py:28-41`
```python
@dataclass
class EntityStats:
    max_health: float = 100.0
    defense: float = 0.0      # All creatures have 0 defense
    attack: float = 0.0        # All creatures have 0 attack
    max_energy: float = 100.0
    entity_vision: float = 50.0
```
**Problem:** Herbivores, carnivores, and omnivores all have identical stats.
**Impact:** Combat is uniform, no species differentiation, no evolutionary niches.

#### 3. ❌ Reproduction System Not Implemented
**Location:** `server/app/simulation/factory/component_factory.py:52`
```python
# Line 52: "TODO: Add ReproductionComponent in future phases"
```
**Problem:** ReproductionComponent exists as a stub but is never added to entities.
**Impact:** Populations can only decrease. Eventual extinction is guaranteed.

#### 4. ⚠️ Plant Respawn is Too Simplistic
**Location:** `server/app/simulation/simulation.py:62-64`
```python
if random.random() < 0.1:  # 10% chance per tick = ~6 plants/second
    self._spawn_random_plant()
```
**Problem:** No carrying capacity. Plants spawn randomly regardless of density.
**Impact:** Resource availability is unpredictable (explosion or depletion).

#### 5. ⚠️ Energy Economy Not Balanced
**Current Values:**
- Plant energy: +15
- Meat energy: +30
- Energy decay: 0.0 (disabled)
- Movement cost: speed × 0.01 × dt

**Problem:** Can't assess balance because energy decay is disabled.
**Impact:** When re-enabled, creatures might starve instantly or become immortal.

#### 6. ❌ No Flee Behavior
**Current Behavior:** Prey stands still and gets attacked until death.
**Problem:** No escape mechanics for herbivores.
**Impact:** Carnivores easily kill all herbivores, leading to both species' extinction.

---

## Fix 1: Re-enable Energy and Hunger System

### Overview
The energy and hunger system is the foundation of all survival mechanics. Without it, creatures have no motivation to seek food, and predator-prey dynamics cannot emerge.

### Current State
```python
# server/app/simulation/core/config.py:21-27
VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.0,  # Comment says "Temporarily disabled for testing"
    "HUNGER_RATE": 0.0,        # Disabled
    "REPRODUCTION_THRESHOLD": 90.0
}
```

### How VitalityComponent Uses These Values
```python
# server/app/simulation/components/base/vitality.py:update()
def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
    # Energy decay (currently = 0.0)
    energy_decay = VITALITY_CONFIG["ENERGY_DECAY_RATE"] * dt
    self.current_energy -= energy_decay

    # Hunger increase when energy is low (currently = 0.0)
    if self.current_energy < self.max_energy * 0.5:
        hunger_increase = VITALITY_CONFIG["HUNGER_RATE"] * dt
        self.hunger += hunger_increase

    # Movement cost (still active)
    physics = owner.get_component('PhysicsComponent')
    if physics:
        movement_cost = physics.velocity.magnitude() * 0.01 * dt
        self.current_energy -= movement_cost
```

**Note:** Movement cost is active, but with 0 decay rate, creatures never run out of energy.

### Proposed Solution

#### Step 1: Calculate Balanced Decay Rates
At 60 FPS, each tick is ~0.0167 seconds.

**Target:** Creatures should survive ~4 seconds without food (gives urgency but not instant death).

```
Time to death = BASE_ENERGY / (ENERGY_DECAY_RATE * 60 FPS)
4 seconds = 100 / (rate * 60)
rate = 100 / (4 * 60) = 0.417

Rounded: 0.4 energy per tick
```

**Hunger calculation:**
```
Hunger should increase when energy < 50%
If creature ignores hunger and continues depleting energy:
- At energy = 0, hunger damage starts (0.5 health per tick when hunger > 75)
- Creature dies in ~200 ticks (3.3 seconds)

Hunger rate: 0.15 per tick
- At energy = 50, hunger starts increasing
- Reaches 75 hunger in (75 / 0.15) = 500 ticks = 8.3 seconds
- Total survival time without food: ~12 seconds (reasonable)
```

#### Step 2: Update Config File
**File:** `server/app/simulation/core/config.py`

```python
VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.4,   # Changed from 0.0 - creatures survive ~4s without food
    "HUNGER_RATE": 0.15,         # Changed from 0.0 - hunger increases when energy low
    "REPRODUCTION_THRESHOLD": 75.0  # Lowered from 90 to make reproduction achievable
}
```

#### Step 3: Test Energy Mechanics
Create test scenarios:
1. **Starvation test:** Spawn creature with no food nearby → should die in ~12 seconds
2. **Survival test:** Spawn creature near food → should eat and survive
3. **Energy recovery:** Creature at low energy eats plant → energy increases, hunger decreases

### Expected Behavior After Fix
- ✅ Creatures actively seek food (visible in DietComponent)
- ✅ Creatures die from starvation if no food available
- ✅ Energy bar depletes visibly over time
- ✅ Eating food restores energy and reduces hunger
- ✅ Herbivores graze on plants regularly
- ✅ Carnivores hunt other creatures for energy

### Files to Modify
1. `server/app/simulation/core/config.py` - Update VITALITY_CONFIG values

### Validation
```python
# server/tests/test_vitality.py (create new test)
def test_energy_decay():
    """Test that energy decreases over time"""
    entity = create_test_entity()
    vitality = entity.get_component('VitalityComponent')
    initial_energy = vitality.current_energy

    # Simulate 1 second (60 ticks)
    for _ in range(60):
        vitality.update(entity, context, dt=1/60)

    # Energy should have decreased
    assert vitality.current_energy < initial_energy

    # Should lose approximately 0.4 * 60 = 24 energy
    energy_lost = initial_energy - vitality.current_energy
    assert 20 < energy_lost < 28  # Allow some variance

def test_starvation_death():
    """Test that creatures die without food"""
    entity = create_test_entity()
    context = create_empty_context()  # No food

    # Simulate until death
    ticks = 0
    max_ticks = 1000  # Safety limit
    while entity.state != EntityState.DEAD and ticks < max_ticks:
        update_entity(entity, context, dt=1/60)
        ticks += 1

    assert entity.state == EntityState.DEAD
    assert ticks < 1000  # Should die before safety limit
    assert 600 < ticks < 800  # Should die around 10-13 seconds
```

---

## Fix 2: Differentiate Species Stats

### Overview
Currently all species (herbivores, carnivores, omnivores) have identical stats. This eliminates strategic diversity and prevents realistic ecosystem dynamics. Herbivores should be fast but weak, carnivores strong but slow, etc.

### Current State
```python
# server/app/simulation/models/entity.py:28-41
@dataclass
class EntityStats:
    max_health: float = 100.0
    current_health: float = 100.0
    defense: float = 0.0        # Same for all
    attack: float = 0.0          # Same for all
    max_energy: float = 100.0
    current_energy: float = 100.0
    entity_vision: float = 50.0
    lifetime: float = float('inf')
```

**Problem:** Entity creation uses these defaults for all creatures. Species traits (HERBIVORE, CARNIVORE, etc.) don't affect stats.

### Species Trait System
```python
# server/app/simulation/core/types.py:10-17
class Trait(str, Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"
    SELF_REPLICATING = "self_replicating"
    TWO_PARENTS = "two_parents"
```

Species have `base_traits: Set[Trait]` but these only affect DietComponent behavior, not stats.

### Proposed Solution

#### Step 1: Design Balanced Stats

**Design Philosophy:**
- Herbivores: Fast, fragile, good vision (spot predators early)
- Carnivores: Strong, tanky, slower (persistence hunters)
- Omnivores: Balanced (Jack of all trades)
- Plants: Stationary, fragile, quick respawn

**Stat Table:**

| Species | Speed | Health | Attack | Defense | Vision | Energy | Strategy |
|---------|-------|--------|--------|---------|--------|--------|----------|
| Herbivore | 15 | 80 | 1 | 2 | 70 | 120 | Flee, graze efficiently |
| Carnivore | 8 | 120 | 10 | 5 | 60 | 100 | Hunt, tank damage |
| Omnivore | 12 | 100 | 5 | 3 | 65 | 110 | Opportunistic, adapt |
| Plant | 0 | 30 | 0 | 0 | 0 | 0 | Reproduce faster than consumed |

**Rationale:**
- **Herbivore speed (15) vs Carnivore speed (8):** Herbivores can escape in straight line, but carnivores can pursue persistently
- **Carnivore attack (10) vs Herbivore defense (2):** Combat damage = (attack - defense) × multiplier, carnivores deal 8 damage vs herbivores
- **Energy pools:** Herbivores need more energy for fleeing, carnivores get large energy boost from kills
- **Vision:** Herbivores see further to spot threats early

#### Step 2: Implement Species-Specific Stats

**File:** `server/app/simulation/models/species.py`

Add method to Species class:

```python
def get_base_stats(self) -> EntityStats:
    """Return species-specific base stats based on traits"""
    from app.simulation.models.entity import EntityStats
    from app.simulation.core.types import Trait

    if Trait.HERBIVORE in self.base_traits:
        return EntityStats(
            max_health=80.0,
            current_health=80.0,
            defense=2.0,
            attack=1.0,
            max_energy=120.0,
            current_energy=120.0,
            entity_vision=70.0,
            lifetime=float('inf')
        )

    elif Trait.CARNIVORE in self.base_traits:
        return EntityStats(
            max_health=120.0,
            current_health=120.0,
            defense=5.0,
            attack=10.0,
            max_energy=100.0,
            current_energy=100.0,
            entity_vision=60.0,
            lifetime=float('inf')
        )

    elif Trait.OMNIVORE in self.base_traits:
        return EntityStats(
            max_health=100.0,
            current_health=100.0,
            defense=3.0,
            attack=5.0,
            max_energy=110.0,
            current_energy=110.0,
            entity_vision=65.0,
            lifetime=float('inf')
        )

    elif Trait.SELF_REPLICATING in self.base_traits:  # Plants
        return EntityStats(
            max_health=30.0,
            current_health=30.0,
            defense=0.0,
            attack=0.0,
            max_energy=0.0,
            current_energy=0.0,
            entity_vision=0.0,
            lifetime=600.0  # 10 seconds instead of 5
        )

    else:
        # Default fallback
        return EntityStats()
```

#### Step 3: Update Entity Creation

**File:** `server/app/simulation/models/species.py`

Modify `create_entity()` method:

```python
def create_entity(self, position: Vector2D) -> 'Entity':
    """Create entity with species-specific stats"""
    from app.simulation.models import Entity
    from app.simulation.models.entity import EntityType

    entity_type = (
        EntityType.PLANT
        if Trait.SELF_REPLICATING in self.base_traits
        else EntityType.CREATURE
    )

    # Get species-specific stats
    stats = self.get_base_stats()

    entity = Entity(
        species_id=self.id,
        type=entity_type,
        position=position,
        traits=self.base_traits.copy(),
        stats=stats  # Use species stats instead of default
    )

    return entity
```

#### Step 4: Update Movement Speeds

**File:** `server/app/simulation/factory/component_factory.py`

Currently, creatures get random speed (1.0-3.0). Change to use species-specific max speed:

```python
def initialize_components(entity: 'Entity', context: 'SimulationContext') -> None:
    from app.simulation.core.types import Trait

    if entity.type == EntityType.CREATURE:
        # Species-specific speed based on traits
        if Trait.HERBIVORE in entity.traits:
            max_speed = 15.0
            initial_speed = random.uniform(12.0, 15.0)
        elif Trait.CARNIVORE in entity.traits:
            max_speed = 8.0
            initial_speed = random.uniform(6.0, 8.0)
        elif Trait.OMNIVORE in entity.traits:
            max_speed = 12.0
            initial_speed = random.uniform(10.0, 12.0)
        else:
            max_speed = 10.0  # Default
            initial_speed = random.uniform(8.0, 10.0)

        # Create initial velocity
        angle = random.uniform(0, 2 * math.pi)
        velocity = Vector2D(
            math.cos(angle) * initial_speed,
            math.sin(angle) * initial_speed
        )

        entity.add_component(PhysicsComponent(
            position=entity.position,
            velocity=velocity,
            max_speed=max_speed,  # Species-specific
            enable_wander=True
        ))

        # ... rest of components
```

### Expected Behavior After Fix
- ✅ Herbivores are visibly faster than carnivores
- ✅ Carnivores deal more damage in combat
- ✅ Herbivores have more energy reserves
- ✅ Combat outcomes vary by species matchup
- ✅ Species occupy different ecological niches

### Files to Modify
1. `server/app/simulation/models/species.py` - Add get_base_stats() method
2. `server/app/simulation/models/species.py` - Update create_entity() to use species stats
3. `server/app/simulation/factory/component_factory.py` - Set species-specific speeds

### Validation
```python
# server/tests/test_species_stats.py
def test_species_have_different_stats():
    """Test that different species have different stats"""
    herbivore_species = create_herbivore_species()
    carnivore_species = create_carnivore_species()

    herb_stats = herbivore_species.get_base_stats()
    carn_stats = carnivore_species.get_base_stats()

    # Herbivores should be faster (this isn't in stats, but in physics)
    # But we can check other stats
    assert herb_stats.attack < carn_stats.attack
    assert herb_stats.max_health < carn_stats.max_health
    assert herb_stats.max_energy > carn_stats.max_energy
    assert herb_stats.entity_vision > carn_stats.entity_vision

def test_combat_damage_varies_by_species():
    """Test that carnivores deal more damage than herbivores"""
    # Create herbivore and carnivore
    herbivore = create_herbivore_entity()
    carnivore = create_carnivore_entity()

    # Simulate carnivore attacking herbivore
    herb_initial_health = herbivore.stats.current_health

    # Mock combat for 1 second
    context = create_test_context([herbivore, carnivore])
    diet = carnivore.get_component('DietComponent')
    for _ in range(60):
        diet.update(carnivore, context, dt=1/60)

    # Herbivore should have taken damage
    assert herbivore.stats.current_health < herb_initial_health
```

---

## Fix 3: Implement Basic Reproduction

### Overview
The ReproductionComponent exists but is never added to entities. This means populations can only decrease, leading to inevitable extinction. Implementing reproduction is critical for long-running simulations.

### Current State
```python
# server/app/simulation/factory/component_factory.py:52
# Line 52 comment:
# TODO: Add ReproductionComponent in future phases
```

**Component exists:** `server/app/simulation/components/base/reproduction.py`
**Status:** Stub implementation with basic structure but no actual logic

### How Reproduction Should Work

#### Reproduction Flow
```
1. Entity checks reproduction conditions every frame:
   - Energy > threshold (75% of max)
   - Cooldown timer expired (10 seconds since last reproduction)
   - Mate available (same species, within range, also ready)

2. Find compatible mate:
   - Same species_id
   - Within 20 units distance
   - Also has energy > threshold
   - Also ready (cooldown expired)

3. Reproduce:
   - Both parents lose 40 energy
   - Child spawned at position near parents (15 unit offset)
   - Child is same species as parents
   - Cooldown resets for both parents

4. Child entity:
   - Full health, full energy
   - Same species and traits as parents
   - Positioned randomly near parents
```

### Proposed Solution

#### Step 1: Complete ReproductionComponent

**File:** `server/app/simulation/components/base/reproduction.py`

```python
from typing import TYPE_CHECKING, Optional
import random
import math
from app.simulation.core.component import Component
from app.simulation.core.config import VITALITY_CONFIG
from app.simulation.core.vector import Vector2D

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class ReproductionComponent(Component):
    """Handles sexual reproduction between entities"""

    def __init__(self, reproduction_cooldown: float = 10.0):
        """
        Args:
            reproduction_cooldown: Seconds between reproduction attempts
        """
        self.reproduction_cooldown = reproduction_cooldown
        self.time_since_last_reproduction = reproduction_cooldown  # Can reproduce immediately if conditions met

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """Check for reproduction opportunities"""
        from app.simulation.models.entity import EntityState

        if owner.state == EntityState.DEAD:
            return

        # Increment cooldown timer
        self.time_since_last_reproduction += dt

        # Check if ready to reproduce
        if self.time_since_last_reproduction < self.reproduction_cooldown:
            return

        # Check energy threshold
        vitality = owner.get_component('VitalityComponent')
        if not vitality:
            return

        reproduction_threshold = VITALITY_CONFIG["REPRODUCTION_THRESHOLD"]
        if vitality.current_energy < reproduction_threshold:
            return

        # Find mate
        mate = self._find_compatible_mate(owner, context)
        if not mate:
            return

        # Reproduce!
        self._create_offspring(owner, mate, context)

        # Reset cooldowns and deduct energy
        self.time_since_last_reproduction = 0.0
        vitality.current_energy -= 40.0

        # Also reset mate's cooldown and energy
        mate_reproduction = mate.get_component('ReproductionComponent')
        mate_vitality = mate.get_component('VitalityComponent')
        if mate_reproduction:
            mate_reproduction.time_since_last_reproduction = 0.0
        if mate_vitality:
            mate_vitality.current_energy -= 40.0

    def _find_compatible_mate(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
        """Find nearby same-species entity that is also ready to reproduce"""
        from app.simulation.models import Entity
        from app.simulation.models.entity import EntityState

        # Search radius
        search_radius = 20.0

        # Query nearby entities
        nearby = context.query_nearby_entities(owner.position, search_radius, exclude_id=owner.id)

        for entity in nearby:
            # Must be same species
            if not isinstance(entity, Entity) or entity.species_id != owner.species_id:
                continue

            # Must be alive
            if entity.state == EntityState.DEAD:
                continue

            # Must have reproduction component
            mate_reproduction = entity.get_component('ReproductionComponent')
            if not mate_reproduction:
                continue

            # Must be ready (cooldown expired)
            if mate_reproduction.time_since_last_reproduction < mate_reproduction.reproduction_cooldown:
                continue

            # Must have enough energy
            mate_vitality = entity.get_component('VitalityComponent')
            if not mate_vitality:
                continue

            reproduction_threshold = VITALITY_CONFIG["REPRODUCTION_THRESHOLD"]
            if mate_vitality.current_energy < reproduction_threshold:
                continue

            # Found compatible mate!
            return entity

        return None

    def _create_offspring(self, parent1: 'Entity', parent2: 'Entity', context: 'SimulationContext') -> None:
        """Spawn child entity near parents"""
        from app.simulation.models import Species, Entity

        # Get parent's species
        species = context.get_by_id(Species, parent1.species_id)
        if not species:
            return

        # Calculate spawn position (random offset from parent1)
        angle = random.uniform(0, 2 * math.pi)
        offset_distance = 15.0
        offset = Vector2D(
            math.cos(angle) * offset_distance,
            math.sin(angle) * offset_distance
        )
        spawn_position = parent1.position + offset

        # Clamp to world bounds
        spawn_position.x = max(0, min(context.width, spawn_position.x))
        spawn_position.y = max(0, min(context.height, spawn_position.y))

        # Create offspring
        offspring = species.create_entity(spawn_position)

        # Register in simulation
        context.register(offspring)

        # Increment species population (create_entity might not do this)
        species.population_count += 1
```

#### Step 2: Add ReproductionComponent to Entities

**File:** `server/app/simulation/factory/component_factory.py`

```python
def initialize_components(entity: 'Entity', context: 'SimulationContext') -> None:
    """Initialize components for an entity based on its type and traits"""
    from app.simulation.components.base.physics import PhysicsComponent
    from app.simulation.components.base.vitality import VitalityComponent
    from app.simulation.components.base.diet import DietComponent
    from app.simulation.components.base.social import SocialComponent
    from app.simulation.components.base.reproduction import ReproductionComponent  # Add import
    from app.simulation.models.entity import EntityType
    from app.simulation.core.types import Trait
    import random
    import math

    # Existing physics setup...

    # Add VitalityComponent (existing)
    if entity.type == EntityType.CREATURE:
        entity.add_component(VitalityComponent())

    # Add DietComponent (existing)
    if entity.type == EntityType.CREATURE:
        entity.add_component(DietComponent())

    # Add SocialComponent (existing)
    if entity.type == EntityType.CREATURE:
        entity.add_component(SocialComponent())

    # ADD ReproductionComponent (NEW!)
    if entity.type == EntityType.CREATURE and Trait.TWO_PARENTS in entity.traits:
        entity.add_component(ReproductionComponent(reproduction_cooldown=10.0))
    elif entity.type == EntityType.PLANT and Trait.SELF_REPLICATING in entity.traits:
        # Plants reproduce asexually (can add separate logic later)
        entity.add_component(ReproductionComponent(reproduction_cooldown=5.0))
```

#### Step 3: Update Simulation Loop to Update Reproduction

**File:** `server/app/simulation/simulation.py`

Ensure ReproductionComponent is updated in the entity update loop:

```python
def _update_entities(self, dt: float) -> None:
    """Update all entities"""
    entities_to_update = list(self.world.get_all(Entity))

    for entity in entities_to_update:
        if entity.state == EntityState.DEAD:
            continue

        # Update components in order
        physics = entity.get_component('PhysicsComponent')
        if physics:
            physics.update(entity, self.world, dt)

        vitality = entity.get_component('VitalityComponent')
        if vitality:
            vitality.update(entity, self.world, dt)

        diet = entity.get_component('DietComponent')
        if diet:
            diet.update(entity, self.world, dt)

        social = entity.get_component('SocialComponent')
        if social:
            social.update(entity, self.world, dt)

        # ADD THIS: Update reproduction component
        reproduction = entity.get_component('ReproductionComponent')
        if reproduction:
            reproduction.update(entity, self.world, dt)
```

### Expected Behavior After Fix
- ✅ Two high-energy entities near each other produce offspring
- ✅ Offspring appears near parents
- ✅ Parents lose energy after reproduction
- ✅ Cooldown prevents continuous reproduction
- ✅ Population can grow instead of only shrinking
- ✅ Simulations can run indefinitely without extinction

### Files to Modify
1. `server/app/simulation/components/base/reproduction.py` - Complete implementation
2. `server/app/simulation/factory/component_factory.py` - Add component to entities
3. `server/app/simulation/simulation.py` - Update component in main loop

### Validation
```python
# server/tests/test_reproduction.py
def test_reproduction_creates_offspring():
    """Test that two ready entities produce offspring"""
    # Create two entities of same species
    species = create_test_species()
    parent1 = species.create_entity(Vector2D(100, 100))
    parent2 = species.create_entity(Vector2D(105, 105))

    # Add components
    initialize_components(parent1, context)
    initialize_components(parent2, context)

    # Set high energy
    parent1.get_component('VitalityComponent').current_energy = 90
    parent2.get_component('VitalityComponent').current_energy = 90

    # Register in context
    context = create_test_context()
    context.register(parent1)
    context.register(parent2)

    initial_entity_count = len(context.get_all(Entity))

    # Update reproduction component
    repro = parent1.get_component('ReproductionComponent')
    repro.update(parent1, context, dt=1.0)

    # Check offspring created
    final_entity_count = len(context.get_all(Entity))
    assert final_entity_count == initial_entity_count + 1

    # Check parents lost energy
    assert parent1.get_component('VitalityComponent').current_energy < 90
    assert parent2.get_component('VitalityComponent').current_energy < 90

def test_reproduction_requires_energy():
    """Test that low-energy entities cannot reproduce"""
    parent1 = create_test_entity()
    parent2 = create_test_entity()

    # Set LOW energy
    parent1.get_component('VitalityComponent').current_energy = 50
    parent2.get_component('VitalityComponent').current_energy = 50

    context = create_test_context([parent1, parent2])
    initial_count = len(context.get_all(Entity))

    repro = parent1.get_component('ReproductionComponent')
    repro.update(parent1, context, dt=1.0)

    # Should NOT reproduce
    assert len(context.get_all(Entity)) == initial_count
```

---

## Fix 4: Fix Plant Spawning

### Overview
Plants currently spawn at a fixed 10% probability per tick (6 plants/second), regardless of existing plant density. This leads to either plant explosion or depletion, with no stable equilibrium.

### Current State
```python
# server/app/simulation/simulation.py:62-64
if random.random() < 0.1:  # 10% chance per tick
    self._spawn_random_plant()

def _spawn_random_plant(self) -> None:
    """Spawn a plant at random position"""
    if not self.plant_species_id:
        return

    plant_species = self.world.get_by_id(Species, self.plant_species_id)
    if not plant_species:
        return

    position = Vector2D(
        random.uniform(0, self.world.width),
        random.uniform(0, self.world.height)
    )

    plant = plant_species.create_entity(position)
    self.world.register(plant)
```

**Problems:**
1. No carrying capacity - plants can spawn infinitely in same area
2. No spatial awareness - might spawn on top of existing plants
3. Rate too high - 6 plants/sec with 50 initial = 410 plants after 1 minute
4. No relationship to consumption - plants spawn even if none are being eaten

### Proposed Solution

#### Carrying Capacity Model
```
Ecological principle: Resources are limited by space and nutrients
Implementation: Max N plants per unit area

Parameters:
- Local radius: 30 units
- Max plants in radius: 5
- Rationale: 30-unit radius = 2827 sq units, 5 plants = 1 plant per 565 sq units
```

#### Density-Based Spawning Algorithm
```python
def _spawn_random_plant(self) -> None:
    """Spawn plants based on local density (carrying capacity)"""
    if not self.plant_species_id:
        return

    plant_species = self.world.get_by_id(Species, self.plant_species_id)
    if not plant_species:
        return

    # Random position candidate
    position = Vector2D(
        random.uniform(0, self.world.width),
        random.uniform(0, self.world.height)
    )

    # Check local plant density
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
```

#### Adjusted Spawn Rate
```python
# In simulation loop, reduce base spawn rate
if random.random() < 0.05:  # Changed from 0.1 to 0.05 (3 plants/sec instead of 6)
    self._spawn_random_plant()
```

**New spawn rate calculation:**
```
Base attempts: 0.05 × 60 FPS = 3 attempts/sec
Success rate: Depends on density (0-100%)
Average: ~50% success = 1.5 plants/sec = 90 plants/minute

With carrying capacity limiting to ~150-200 plants total:
- Initial: 50 plants
- After 1 min: ~140 plants (high success rate in empty areas)
- After 2 min: ~180 plants (lower success rate as areas fill)
- Equilibrium: ~200 plants (low success rate, balanced by consumption)
```

### Alternative: Respawn at Death Location
```python
# When plant is eaten, remember location and respawn there after delay
class PlantRespawnSystem:
    def __init__(self):
        self.respawn_queue = []  # List of (position, time_remaining)

    def on_plant_death(self, plant_position: Vector2D):
        """Queue plant for respawn at same location"""
        respawn_delay = 10.0  # 10 seconds
        self.respawn_queue.append((plant_position, respawn_delay))

    def update(self, dt: float):
        """Tick down respawn timers and spawn plants"""
        for i in range(len(self.respawn_queue) - 1, -1, -1):
            position, time_remaining = self.respawn_queue[i]
            time_remaining -= dt

            if time_remaining <= 0:
                self._spawn_plant_at(position)
                self.respawn_queue.pop(i)
            else:
                self.respawn_queue[i] = (position, time_remaining)
```

### Expected Behavior After Fix
- ✅ Plant population stabilizes around carrying capacity (150-200)
- ✅ Depleted areas slowly regrow
- ✅ Dense areas don't get denser
- ✅ Herbivore population correlates with plant availability
- ✅ No more plant explosions to thousands

### Files to Modify
1. `server/app/simulation/simulation.py` - Update `_spawn_random_plant()` method
2. `server/app/simulation/simulation.py` - Reduce spawn rate from 0.1 to 0.05

### Validation
```python
# server/tests/test_plant_spawning.py
def test_plant_carrying_capacity():
    """Test that plants don't spawn in dense areas"""
    context = create_test_context()
    plant_species = create_plant_species()

    # Fill a local area with 5 plants
    center = Vector2D(500, 500)
    for _ in range(5):
        offset = Vector2D(random.uniform(-20, 20), random.uniform(-20, 20))
        plant = plant_species.create_entity(center + offset)
        context.register(plant)

    # Try to spawn many plants at center (should fail due to density)
    initial_count = len([e for e in context.get_all(Entity) if e.species_id == plant_species.id])

    simulation = Simulation(context)
    for _ in range(1000):  # Try 1000 times
        if random.random() < 1.0:  # Always try (for testing)
            simulation._spawn_plant_at_position(center, plant_species.id)

    final_count = len([e for e in context.get_all(Entity) if e.species_id == plant_species.id])

    # Should not have spawned any (or very few) new plants
    assert final_count <= initial_count + 2

def test_plant_population_stabilizes():
    """Test that plant population reaches equilibrium"""
    context = create_test_context()
    simulation = Simulation(context)

    # Start with 50 plants
    population_over_time = []

    # Run for 2 minutes
    for tick in range(60 * 60 * 2):
        simulation.update(1/60)

        if tick % 60 == 0:  # Record every second
            plant_count = len([e for e in context.get_all(Entity) if e.type == EntityType.PLANT])
            population_over_time.append(plant_count)

    # Check that population stabilized (last 10 readings should be similar)
    late_population = population_over_time[-10:]
    avg_late = sum(late_population) / len(late_population)
    variance = sum((p - avg_late) ** 2 for p in late_population) / len(late_population)

    assert variance < 100  # Low variance = stable
    assert 100 < avg_late < 300  # Reasonable population size
```

---

## Fix 5: Balance Energy Economy

### Overview
With energy decay currently disabled, we can't assess whether food energy values, movement costs, and consumption rates are balanced. Once energy is re-enabled (Fix #1), we need to tune these values so that:
- Herbivores can sustain themselves on plants
- Carnivores can sustain themselves on prey
- Neither species finds survival trivial or impossible

### Current Values
```python
# Energy sources (in DietComponent)
PLANT_ENERGY_VALUE = 15
MEAT_ENERGY_VALUE = 30

# Hunger reduction (in DietComponent)
HUNGER_REDUCTION_FROM_EATING = 50

# Energy costs (in VitalityComponent)
energy_decay = 0.0 per tick (DISABLED)
movement_cost = speed × 0.01 × dt
hunger_damage = 0.5 health per tick when hunger > 75
energy_depletion_damage = 1.0 health per tick when energy ≤ 0
```

### Energy Budget Analysis

#### Herbivore Energy Budget (After Re-enabling Decay)
```
Energy capacity: 120
Energy decay rate: 0.4 per tick = 24 per second
Movement cost (at speed 15): 15 × 0.01 × 1/60 = 0.0025 per tick = 0.15 per second
Total drain: 24.15 energy per second

Plant energy value: 15
Time to find and eat plant: ~2 seconds (seek + consume)
Energy spent finding plant: 2 × 24.15 = 48.3
Net gain: 15 - 48.3 = -33.3 (NEGATIVE!)

PROBLEM: Herbivores lose energy faster than they can recover it!
```

#### Proposed Balanced Values

**Increase food energy values:**
```python
PLANT_ENERGY_VALUE = 25  # Increased from 15
MEAT_ENERGY_VALUE = 45   # Increased from 30
```

**New herbivore budget:**
```
Energy drain: 24.15 per second
Time to find plant: 2 seconds
Energy spent: 48.3
Plant energy value: 25
Net gain: 25 - 48.3 = -23.3 (still negative, but herbivore eats multiple plants)

Eating frequency: Every 3 seconds (average)
Energy gained per 3 sec: 25
Energy spent per 3 sec: 24.15 × 3 = 72.45
Plants needed: 72.45 / 25 = 2.9 plants per 3 seconds

With plant population: 200 plants
Herbivore population sustainable: 200 / (2.9 × 20 herbivores) = ~70 seconds before depletion
BUT plants respawn at 1.5/sec = 4.5 plants per 3 sec
Net plant change: 4.5 spawn - 2.9 consumed = +1.6 plants per 3 sec (sustainable!)
```

**Carnivore budget:**
```
Energy capacity: 100
Energy drain: 0.4 + (8 × 0.01) = 0.48 per tick = 28.8 per second

Time to hunt herbivore: ~10 seconds (chase + kill)
Energy spent hunting: 10 × 28.8 = 288
Meat energy value: 45
Net gain: 45 - 288 = -243 (VERY NEGATIVE!)

PROBLEM: Carnivores can't survive on 45 energy kills when hunts cost 288 energy!

Solution: Increase meat energy value
MEAT_ENERGY_VALUE = 60  # Increased from 45

New budget:
Net per kill: 60 - 288 = -228 (still negative)
Kills needed per 10 sec: 288 / 60 = 4.8 kills (IMPOSSIBLE)

Better solution: Reduce hunt time by improving carnivore AI, OR make prey easier to catch
```

#### Better Approach: Adjust Energy Decay
```python
# Reduce energy decay rate to make survival easier
VITALITY_CONFIG = {
    "ENERGY_DECAY_RATE": 0.2,  # Reduced from 0.4
    "HUNGER_RATE": 0.1,         # Reduced from 0.15
}

New herbivore budget:
Energy drain: 12.075 per second (instead of 24.15)
Energy spent per 3 sec: 36.225
Plants needed: 36.225 / 25 = 1.45 plants per 3 seconds (achievable!)

New carnivore budget:
Energy drain: 14.4 per second (instead of 28.8)
Energy spent per 10 sec hunt: 144
Meat value: 60
Net per kill: 60 - 144 = -84
Kills needed: 144 / 60 = 2.4 kills per 10 seconds (still hard but possible with pack hunting)
```

### Proposed Solution

#### Step 1: Update Energy Values
**File:** `server/app/simulation/components/base/diet.py`

```python
# Around line 40-50 where energy values are defined
PLANT_ENERGY_VALUE = 25.0   # Increased from 15
MEAT_ENERGY_VALUE = 60.0    # Increased from 30
HUNGER_REDUCTION = 30.0     # Reduced from 50 (eating doesn't fully satisfy)
```

#### Step 2: Adjust Energy Decay Rate
**File:** `server/app/simulation/core/config.py`

```python
VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.2,   # Reduced from 0.4 for balance
    "HUNGER_RATE": 0.1,          # Reduced from 0.15
    "REPRODUCTION_THRESHOLD": 75.0
}
```

#### Step 3: Reduce Hunger Damage (Optional)
**File:** `server/app/simulation/components/base/vitality.py`

```python
# Around line 80-85 where hunger damage is applied
if self.hunger > 75:
    hunger_damage = 0.3 * dt  # Reduced from 0.5
    self.current_health -= hunger_damage
```

### Tuning Process
1. Re-enable energy decay at 0.2 rate
2. Observe herbivore survival time (target: 30-60 seconds average)
3. If herbivores die too quickly: increase plant energy value or reduce decay rate
4. If herbivores never die: decrease plant energy value or increase decay rate
5. Repeat for carnivores

### Expected Behavior After Fix
- ✅ Herbivores survive 30-60 seconds on average
- ✅ Herbivores actively graze (eat every 3-5 seconds)
- ✅ Carnivores catch prey before starving
- ✅ Both populations remain stable for 10+ minutes
- ✅ Energy bars show meaningful fluctuation (not always full or empty)

### Files to Modify
1. `server/app/simulation/components/base/diet.py` - Update energy values
2. `server/app/simulation/core/config.py` - Adjust decay rates
3. `server/app/simulation/components/base/vitality.py` - (Optional) Reduce hunger damage

### Validation
```python
# server/tests/test_energy_balance.py
def test_herbivore_survival_time():
    """Test that herbivores survive reasonable time with plants"""
    context = create_test_context()

    # Spawn herbivore and nearby plants
    herbivore = create_herbivore_entity()
    for _ in range(10):
        plant = create_plant_entity(position_near(herbivore.position))
        context.register(plant)

    context.register(herbivore)

    # Run simulation until herbivore dies
    survival_time = 0.0
    max_time = 120.0  # 2 minutes max

    while herbivore.state != EntityState.DEAD and survival_time < max_time:
        update_entity(herbivore, context, dt=1/60)
        survival_time += 1/60

    # Should survive at least 30 seconds with nearby food
    assert survival_time >= 30.0
    print(f"Herbivore survived: {survival_time:.1f} seconds")

def test_energy_economy_sustainability():
    """Test that ecosystem is energetically sustainable"""
    context = create_test_context()

    # Spawn balanced ecosystem
    for _ in range(50):
        context.register(create_plant_entity())
    for _ in range(20):
        context.register(create_herbivore_entity())
    for _ in range(8):
        context.register(create_carnivore_entity())

    # Run for 5 minutes
    for _ in range(60 * 60 * 5):
        simulation.update(1/60)

    # Check populations still exist
    herbivores = [e for e in context.get_all(Entity) if Trait.HERBIVORE in e.traits]
    carnivores = [e for e in context.get_all(Entity) if Trait.CARNIVORE in e.traits]

    assert len(herbivores) > 5  # Some herbivores survived
    assert len(carnivores) > 2  # Some carnivores survived
```

---

## Fix 6: Add Flee Behavior

### Overview
Currently, prey species (herbivores) don't flee from predators. They just stand there and get attacked until death. This makes hunting trivial and leads to rapid extinction of herbivores.

### Current State
**DietComponent** handles both seeking food and attacking, but there's no defensive behavior. When a carnivore approaches a herbivore:
1. Carnivore's DietComponent sees herbivore as food
2. Carnivore attacks herbivore
3. Herbivore continues wandering or eating
4. Herbivore dies

**No flee behavior exists in any component.**

### Predator-Prey Dynamics Theory
```
Successful ecosystems have:
- Predators that sometimes succeed in hunts
- Prey that sometimes escape

Escape mechanics:
- Speed advantage (herbivores faster than carnivores) ✅ Done in Fix #2
- Early detection (herbivores have better vision) ✅ Done in Fix #2
- Flee behavior (run away from threats) ❌ MISSING
```

### Proposed Solution

#### Option 1: Add Flee Logic to PhysicsComponent
**File:** `server/app/simulation/components/base/physics.py`

```python
def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
    """Update physics with flee behavior"""
    from app.simulation.core.types import Trait

    # Check for nearby threats (predators)
    threat = self._detect_nearby_threat(owner, context)

    if threat:
        # FLEE from threat (highest priority)
        flee_direction = (owner.position - threat.position).normalized()
        flee_force = flee_direction * self.max_force * 2.0  # Strong flee impulse
        self.velocity += flee_force * dt
    else:
        # Normal behavior (wander, cohesion, etc.)
        # ... existing physics code ...
```

**Helper method:**
```python
def _detect_nearby_threat(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
    """Detect nearby predators"""
    from app.simulation.core.types import Trait

    # Only herbivores flee
    if Trait.HERBIVORE not in owner.traits:
        return None

    # Check if low health or low energy (heightened fear)
    vitality = owner.get_component('VitalityComponent')
    if vitality:
        is_vulnerable = (vitality.current_health < vitality.max_health * 0.5 or
                        vitality.current_energy < vitality.max_energy * 0.3)
    else:
        is_vulnerable = False

    # Search for predators
    detection_radius = owner.stats.entity_vision  # Use vision stat
    nearby = context.query_nearby_entities(owner.position, detection_radius, exclude_id=owner.id)

    for entity in nearby:
        # Is this a predator?
        if Trait.CARNIVORE in entity.traits or Trait.OMNIVORE in entity.traits:
            # Always flee if vulnerable, otherwise flee if very close
            distance = owner.position.distance_to(entity.position)

            if is_vulnerable or distance < 30.0:
                return entity  # Found a threat!

    return None
```

#### Option 2: Create Dedicated FleeComponent
**New File:** `server/app/simulation/components/base/flee.py`

```python
from typing import TYPE_CHECKING, Optional
from app.simulation.core.component import Component
from app.simulation.core.types import Trait

if TYPE_CHECKING:
    from app.simulation.models import Entity
    from app.simulation.core.context import SimulationContext

class FleeComponent(Component):
    """Handles fleeing from predators"""

    def __init__(self, fear_threshold: float = 0.5):
        """
        Args:
            fear_threshold: Health ratio below which entity becomes afraid
        """
        self.fear_threshold = fear_threshold
        self.current_threat: Optional['Entity'] = None

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        """Check for threats and flee if necessary"""
        # Only prey species flee
        if Trait.HERBIVORE not in owner.traits:
            return

        # Detect threats
        self.current_threat = self._find_nearest_threat(owner, context)

        if self.current_threat:
            self._flee_from_threat(owner)

    def _find_nearest_threat(self, owner: 'Entity', context: 'SimulationContext') -> Optional['Entity']:
        """Find nearest predator"""
        detection_radius = owner.stats.entity_vision
        nearby = context.query_nearby_entities(owner.position, detection_radius, exclude_id=owner.id)

        threats = []
        for entity in nearby:
            if self._is_threat(entity):
                distance = owner.position.distance_to(entity.position)
                threats.append((distance, entity))

        if not threats:
            return None

        # Return closest threat
        threats.sort(key=lambda x: x[0])
        return threats[0][1]

    def _is_threat(self, entity: 'Entity') -> bool:
        """Check if entity is a predator"""
        return Trait.CARNIVORE in entity.traits or Trait.OMNIVORE in entity.traits

    def _flee_from_threat(self, owner: 'Entity') -> None:
        """Set velocity to flee from threat"""
        physics = owner.get_component('PhysicsComponent')
        if not physics or not self.current_threat:
            return

        # Calculate flee direction (away from threat)
        flee_direction = (owner.position - self.current_threat.position).normalized()

        # Set velocity to maximum speed in flee direction
        physics.velocity = flee_direction * physics.max_speed
```

**Add to component factory:**
```python
# In initialize_components():
if entity.type == EntityType.CREATURE and Trait.HERBIVORE in entity.traits:
    entity.add_component(FleeComponent())
```

### Recommended Approach
**Use Option 1** (add to PhysicsComponent) because:
- Simpler implementation
- Flee is a movement behavior, physics handles movement
- Fewer components to manage
- Already has access to velocity and forces

### Flee Behavior Parameters
```python
FLEE_DETECTION_RADIUS = entity_vision  # Herbivores: 70, Carnivores: 60
FLEE_ACTIVATION_DISTANCE = 30.0  # Start fleeing when predator within 30 units
FLEE_FORCE_MULTIPLIER = 2.0  # Flee force is 2x normal max force
VULNERABLE_HEALTH_THRESHOLD = 0.5  # Below 50% health = always flee
VULNERABLE_ENERGY_THRESHOLD = 0.3  # Below 30% energy = always flee
```

### Expected Behavior After Fix
- ✅ Herbivores flee when carnivores approach
- ✅ Herbivores flee sooner when low health/energy
- ✅ Herbivores use speed advantage to escape
- ✅ Carnivores must chase prey (hunting is challenging)
- ✅ Some prey escape, some get caught (realistic)
- ✅ Herbivore population survives longer

### Files to Modify
1. `server/app/simulation/components/base/physics.py` - Add threat detection and flee logic

### Validation
```python
# server/tests/test_flee_behavior.py
def test_herbivore_flees_from_carnivore():
    """Test that herbivores flee when carnivore approaches"""
    herbivore = create_herbivore_entity(position=Vector2D(100, 100))
    carnivore = create_carnivore_entity(position=Vector2D(120, 100))

    context = create_test_context([herbivore, carnivore])

    # Record initial distance
    initial_distance = herbivore.position.distance_to(carnivore.position)

    # Update for 2 seconds
    for _ in range(120):
        physics = herbivore.get_component('PhysicsComponent')
        physics.update(herbivore, context, dt=1/60)

    # Distance should have increased (herbivore fled)
    final_distance = herbivore.position.distance_to(carnivore.position)
    assert final_distance > initial_distance

def test_healthy_herbivore_ignores_distant_predator():
    """Test that healthy herbivores don't flee from distant predators"""
    herbivore = create_herbivore_entity(position=Vector2D(100, 100))
    carnivore = create_carnivore_entity(position=Vector2D(200, 100))  # 100 units away

    # Set herbivore to full health
    herbivore.get_component('VitalityComponent').current_health = 80.0

    context = create_test_context([herbivore, carnivore])

    physics = herbivore.get_component('PhysicsComponent')
    threat = physics._detect_nearby_threat(herbivore, context)

    # Should not detect threat (too far away)
    assert threat is None
```

---

## Testing Strategy

### Unit Tests
Create test files for each fix:

1. **`tests/test_energy_system.py`**
   - test_energy_decay_over_time()
   - test_hunger_increases_when_energy_low()
   - test_starvation_causes_death()
   - test_eating_restores_energy()

2. **`tests/test_species_stats.py`**
   - test_herbivore_stats_differ_from_carnivore()
   - test_species_speed_differences()
   - test_combat_damage_varies_by_species()

3. **`tests/test_reproduction.py`**
   - test_reproduction_creates_offspring()
   - test_reproduction_requires_energy()
   - test_reproduction_cooldown()
   - test_mate_finding()

4. **`tests/test_plant_spawning.py`**
   - test_plant_carrying_capacity()
   - test_plant_population_stabilizes()
   - test_plants_dont_spawn_on_plants()

5. **`tests/test_energy_balance.py`**
   - test_herbivore_survival_time()
   - test_carnivore_can_sustain_on_prey()
   - test_energy_economy_sustainability()

6. **`tests/test_flee_behavior.py`**
   - test_herbivore_flees_from_carnivore()
   - test_flee_direction_is_away_from_threat()
   - test_vulnerable_entities_flee_sooner()

### Integration Tests
**File:** `tests/test_ecosystem_integration.py`

```python
def test_full_ecosystem_survives_5_minutes():
    """Test that balanced ecosystem survives without extinction"""
    context = create_balanced_ecosystem()

    # Run for 5 minutes
    for _ in range(60 * 60 * 5):
        simulation.update(1/60)

    # All species should still exist
    plants = count_entities_by_type(context, EntityType.PLANT)
    herbivores = count_entities_with_trait(context, Trait.HERBIVORE)
    carnivores = count_entities_with_trait(context, Trait.CARNIVORE)

    assert plants > 20
    assert herbivores > 5
    assert carnivores > 2

def test_predator_prey_dynamics():
    """Test that predator-prey population cycles emerge"""
    context = create_test_context()

    # Track populations over time
    populations = {'herbivore': [], 'carnivore': []}

    for tick in range(60 * 60 * 10):  # 10 minutes
        simulation.update(1/60)

        if tick % 60 == 0:  # Record every second
            populations['herbivore'].append(count_herbivores(context))
            populations['carnivore'].append(count_carnivores(context))

    # Check for population cycles (boom and bust)
    herb_max = max(populations['herbivore'])
    herb_min = min(populations['herbivore'])

    assert herb_max > herb_min * 2  # At least 2x difference (indicates cycles)
```

### Manual Testing Scenarios

#### Scenario 1: Energy System Verification
```
1. Start simulation with default species
2. Watch creature energy bars
3. Verify:
   - Energy decreases over time
   - Hunger increases when energy < 50%
   - Creatures seek food when hungry
   - Eating restores energy
   - Creatures die if starved
```

#### Scenario 2: Species Differentiation
```
1. Spawn 1 herbivore, 1 carnivore side-by-side
2. Observe:
   - Herbivore moves faster
   - Carnivore catches up slowly (if hunting)
   - Combat damage varies
3. Check stats in UI:
   - Different attack values
   - Different health pools
```

#### Scenario 3: Reproduction
```
1. Spawn 2 herbivores near each other
2. Wait for energy > 75%
3. Verify:
   - Offspring appears near parents
   - Parents lose energy
   - Population count increases
4. Wait 10 seconds (cooldown)
5. Verify reproduction can happen again
```

#### Scenario 4: Plant Balance
```
1. Start simulation with 50 plants
2. Run for 5 minutes
3. Record plant count every 30 seconds
4. Verify:
   - Count stabilizes (doesn't explode or crash)
   - Range: 100-250 plants
5. Spawn 50 herbivores
6. Verify plants still regrow (don't go extinct)
```

#### Scenario 5: Energy Balance
```
1. Spawn 10 herbivores with abundant plants
2. Track average survival time
3. Target: 30-60 seconds per herbivore
4. Adjust energy values if too short/long
5. Repeat for carnivores hunting herbivores
```

#### Scenario 6: Flee Behavior
```
1. Spawn 1 herbivore, 1 carnivore
2. Move carnivore toward herbivore
3. Verify:
   - Herbivore flees when carnivore within 30 units
   - Herbivore runs at max speed
   - Direction is away from carnivore
4. Lower herbivore health to 30%
5. Verify herbivore flees from further away
```

### Performance Testing
```python
# tests/test_performance.py
def test_500_entity_performance():
    """Ensure simulation maintains 60 FPS with 500 entities"""
    context = create_test_context()

    # Spawn 500 entities
    for _ in range(500):
        entity = create_random_entity()
        context.register(entity)

    # Measure frame time
    import time
    iterations = 100
    start = time.perf_counter()

    for _ in range(iterations):
        simulation.update(1/60)

    elapsed = time.perf_counter() - start
    avg_frame_time = (elapsed / iterations) * 1000  # ms

    assert avg_frame_time < 16  # Must be under 16ms for 60 FPS
    print(f"Average frame time: {avg_frame_time:.2f}ms")
```

---

## Success Criteria

All 6 fixes must meet these criteria before moving to next phase:

### Fix 1: Energy and Hunger ✅
- [ ] Energy decreases over time (visible in UI)
- [ ] Hunger increases when energy < 50%
- [ ] Creatures die from starvation without food
- [ ] Eating food restores energy and reduces hunger
- [ ] Unit tests pass for energy decay and starvation

### Fix 2: Species Stats ✅
- [ ] Herbivores have speed 15, carnivores have speed 8
- [ ] Attack values differ (herbivore 1, carnivore 10)
- [ ] Combat damage varies based on species matchup
- [ ] Stats visible in entity inspector UI
- [ ] Unit tests pass for species differentiation

### Fix 3: Reproduction ✅
- [ ] Two high-energy entities produce offspring
- [ ] Offspring appears near parents (within 20 units)
- [ ] Parents lose 40 energy each
- [ ] Cooldown prevents continuous reproduction (10 sec)
- [ ] Population count increases over time
- [ ] Unit tests pass for reproduction logic

### Fix 4: Plant Spawning ✅
- [ ] Plant population stabilizes (not exponential growth)
- [ ] Target range: 100-250 plants
- [ ] Dense areas don't spawn more plants
- [ ] Depleted areas regrow over time
- [ ] Unit tests pass for carrying capacity

### Fix 5: Energy Balance ✅
- [ ] Herbivores survive 30-60 seconds average with food
- [ ] Carnivores can sustain on prey
- [ ] Both populations survive 5+ minutes
- [ ] Energy bars fluctuate (not always full/empty)
- [ ] Integration tests pass for ecosystem sustainability

### Fix 6: Flee Behavior ✅
- [ ] Herbivores flee when carnivores approach (<30 units)
- [ ] Flee direction is away from predator
- [ ] Flee speed equals max speed (15 for herbivores)
- [ ] Some prey escape, some get caught (50/50 balance)
- [ ] Unit tests pass for flee detection and behavior

### Overall Ecosystem Health ✅
- [ ] All species survive 10+ minutes without extinction
- [ ] Population cycles observable (boom and bust)
- [ ] Predator-prey dynamics emerge naturally
- [ ] Simulation runs at 60 FPS with 500 entities
- [ ] No crashes or errors during 30-minute run

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review this plan with team
- [ ] Set up test environment
- [ ] Create feature branch: `feature/phase0-critical-fixes`
- [ ] Back up current simulation state

### Implementation Order
1. [ ] **Fix 1: Re-enable Energy** (2-3 hours)
   - [ ] Update config.py values
   - [ ] Test energy decay
   - [ ] Adjust decay rate if needed

2. [ ] **Fix 2: Differentiate Species** (3-4 hours)
   - [ ] Add get_base_stats() to Species
   - [ ] Update entity creation
   - [ ] Update component factory for speeds
   - [ ] Test in UI

3. [ ] **Fix 3: Implement Reproduction** (4-5 hours)
   - [ ] Complete ReproductionComponent
   - [ ] Add to component factory
   - [ ] Update simulation loop
   - [ ] Test offspring creation

4. [ ] **Fix 4: Fix Plant Spawning** (2-3 hours)
   - [ ] Update _spawn_random_plant() logic
   - [ ] Add carrying capacity check
   - [ ] Reduce spawn rate
   - [ ] Test population stabilization

5. [ ] **Fix 5: Balance Energy Economy** (3-4 hours)
   - [ ] Update energy values in diet.py
   - [ ] Adjust decay rates
   - [ ] Run balance tests
   - [ ] Iterate on values

6. [ ] **Fix 6: Add Flee Behavior** (2-3 hours)
   - [ ] Add threat detection to PhysicsComponent
   - [ ] Implement flee logic
   - [ ] Test predator-prey chases
   - [ ] Tune detection/activation thresholds

### Post-Implementation
- [ ] Run all unit tests
- [ ] Run integration tests
- [ ] Manual testing scenarios (all 6)
- [ ] Performance testing (500 entities, 60 FPS)
- [ ] Update documentation
- [ ] Create PR with summary
- [ ] Code review
- [ ] Merge to main
- [ ] Deploy to staging
- [ ] Validate on staging
- [ ] Deploy to production

---

## Timeline Estimate

| Fix | Time Estimate | Dependencies |
|-----|---------------|--------------|
| Fix 1: Energy System | 2-3 hours | None |
| Fix 2: Species Stats | 3-4 hours | None |
| Fix 3: Reproduction | 4-5 hours | Fix 1 (energy) |
| Fix 4: Plant Spawning | 2-3 hours | None |
| Fix 5: Energy Balance | 3-4 hours | Fix 1, 4 (need energy enabled and plants stable) |
| Fix 6: Flee Behavior | 2-3 hours | Fix 2 (speed differences) |
| **Testing & Integration** | 4-6 hours | All fixes |
| **Total** | **20-28 hours** | **2-3 days** |

### Recommended Schedule
**Day 1 (8 hours):**
- Morning: Fix 1 + Fix 2
- Afternoon: Fix 3 + Fix 4

**Day 2 (8 hours):**
- Morning: Fix 5 (balance tuning)
- Afternoon: Fix 6 + initial testing

**Day 3 (8 hours):**
- Full day: Comprehensive testing, bug fixes, documentation

---

## Conclusion

These 6 critical fixes will transform the simulation from broken to functional. The ecosystem will exhibit:
- **Realistic survival mechanics** (energy, hunger, death)
- **Species diversity** (different strategies for different species)
- **Population dynamics** (growth, competition, predator-prey cycles)
- **Emergent behavior** (fleeing, hunting, reproducing)
- **Long-term stability** (no inevitable extinction)

Once Phase 0 is complete, the simulation will be a solid foundation for future enhancements (genetic evolution, neural networks, user-created species, etc.).

---

**Document Owner:** Development Team
**Last Updated:** 2025-10-18
**Status:** Ready for Implementation
