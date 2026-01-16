# Phase 0: Critical System Fixes - Progress Tracker

**Last Updated:** 2025-10-19
**Status:** Implementation Complete - Ready for Testing
**Overall Completion:** 6/6 fixes complete
**Time Estimate:** 2-3 days (20-28 hours)

---

## Progress Legend
- 🔴 **Not Started** - Task not yet begun
- 🟡 **In Progress** - Currently working on this task
- 🟢 **Complete** - Task finished and tested
- ⚠️ **Blocked** - Waiting on dependency or issue
- ⏭️ **Skipped** - Intentionally skipped (note reason)

---

## Quick Status Overview

| Fix # | Fix Name | Status | Completion | Est. Time | Priority |
|-------|----------|--------|------------|-----------|----------|
| Fix 1 | Re-enable Energy & Hunger | 🟢 Complete | 6/6 | 2-3 hours | CRITICAL |
| Fix 2 | Differentiate Species Stats | 🟢 Complete | 7/7 | 3-4 hours | CRITICAL |
| Fix 3 | Implement Reproduction | 🟢 Complete | 8/8 | 4-5 hours | CRITICAL |
| Fix 4 | Fix Plant Spawning | 🟢 Complete | 5/5 | 2-3 hours | HIGH |
| Fix 5 | Balance Energy Economy | 🟢 Complete | 6/6 | 3-4 hours | HIGH |
| Fix 6 | Add Flee Behavior | 🟢 Complete | 5/5 | 2-3 hours | HIGH |

**Total Tasks:** 37/37 complete ✅

---

## Fix 1: Re-enable Energy and Hunger System

**Priority:** CRITICAL
**Status:** 🔴 Not Started
**Time Estimate:** 2-3 hours
**Completion:** 0/6 tasks

### Background
Energy and hunger systems are currently disabled (set to 0.0 in config). This prevents creatures from needing to eat, eliminating all survival mechanics and predator-prey dynamics.

### Tasks

#### 1.1 Update Configuration Values 🔴
**File:** `server/app/simulation/core/config.py`
- [ ] Change `ENERGY_DECAY_RATE` from `0.0` to `0.4`
- [ ] Change `HUNGER_RATE` from `0.0` to `0.15`
- [ ] Change `REPRODUCTION_THRESHOLD` from `90.0` to `75.0`
- [ ] Commit changes with message: "Re-enable energy and hunger systems"

**Location:** Lines 24-25
**Expected result:** Creatures lose ~24 energy per second, survive ~4 seconds without food

---

#### 1.2 Test Energy Decay 🔴
**File:** `server/tests/test_vitality.py` (create new test file)
- [ ] Create test: `test_energy_decay_over_time()`
  - Spawn entity with full energy
  - Simulate 60 ticks (1 second)
  - Verify energy decreased by ~24 (allow 20-28 range)
- [ ] Create test: `test_hunger_increases_when_energy_low()`
  - Set entity energy to 40% (below 50% threshold)
  - Simulate 100 ticks
  - Verify hunger increased
- [ ] Run tests: `uv run pytest server/tests/test_vitality.py -v`

**Expected result:** Tests pass, confirming energy decay works

---

#### 1.3 Test Starvation Death 🔴
**File:** `server/tests/test_vitality.py`
- [ ] Create test: `test_starvation_causes_death()`
  - Spawn entity in empty environment (no food)
  - Simulate until death or 1000 ticks
  - Verify entity dies
  - Verify death occurs around 600-800 ticks (10-13 seconds)
- [ ] Run test

**Expected result:** Entities die from starvation without food

---

#### 1.4 Test Energy Restoration from Eating 🔴
**File:** `server/tests/test_vitality.py`
- [ ] Create test: `test_eating_restores_energy()`
  - Spawn entity with low energy (30)
  - Spawn plant nearby
  - Simulate until entity eats plant
  - Verify energy increased
- [ ] Run test

**Expected result:** Eating food restores energy

---

#### 1.5 Manual Testing 🔴
- [ ] Start simulation with default species
- [ ] Watch creature energy bars in UI
- [ ] Verify energy decreases over time (visible)
- [ ] Verify creatures actively seek food
- [ ] Verify creatures die if no food available
- [ ] Record observations in issue/PR comments

**Expected result:** Energy system visibly functioning in UI

---

#### 1.6 Balance Tuning (if needed) 🔴
- [ ] If creatures die too quickly (< 2 seconds): reduce decay rate to 0.3
- [ ] If creatures never die: increase decay rate to 0.5
- [ ] Run 5-minute simulation to verify balance
- [ ] Document final values in PR

**Expected result:** Creatures survive 3-5 seconds without food (urgent but not instant death)

---

### Success Criteria
- ✅ Energy decreases over time (visible in UI)
- ✅ Hunger increases when energy < 50%
- ✅ Creatures die from starvation without food
- ✅ Eating food restores energy and reduces hunger
- ✅ Unit tests pass

### Files Modified
- `server/app/simulation/core/config.py`
- `server/tests/test_vitality.py` (new file)

---

## Fix 2: Differentiate Species Stats

**Priority:** CRITICAL
**Status:** 🔴 Not Started
**Time Estimate:** 3-4 hours
**Completion:** 0/7 tasks
**Dependencies:** None

### Background
All species currently have identical stats (attack=0, defense=0, etc.). This eliminates strategic diversity and prevents realistic ecosystem dynamics.

### Tasks

#### 2.1 Add get_base_stats() Method to Species 🔴
**File:** `server/app/simulation/models/species.py`
- [ ] Add `get_base_stats(self) -> EntityStats` method
- [ ] Implement herbivore stats branch:
  - max_health: 80, attack: 1, defense: 2, vision: 70, energy: 120
- [ ] Implement carnivore stats branch:
  - max_health: 120, attack: 10, defense: 5, vision: 60, energy: 100
- [ ] Implement omnivore stats branch:
  - max_health: 100, attack: 5, defense: 3, vision: 65, energy: 110
- [ ] Implement plant stats branch:
  - max_health: 30, all others: 0, lifetime: 600
- [ ] Add default fallback for unknown traits

**Expected result:** Method returns species-appropriate stats

---

#### 2.2 Update Entity Creation to Use Species Stats 🔴
**File:** `server/app/simulation/models/species.py`
- [ ] Modify `create_entity()` method
- [ ] Call `stats = self.get_base_stats()`
- [ ] Pass `stats` parameter to Entity constructor
- [ ] Test: Create herbivore entity, verify stats.attack == 1
- [ ] Test: Create carnivore entity, verify stats.attack == 10

**Expected result:** Entities created with species-specific stats

---

#### 2.3 Update PhysicsComponent for Species-Specific Speeds 🔴
**File:** `server/app/simulation/factory/component_factory.py`
- [ ] In `initialize_components()`, add speed logic:
  - Herbivore: max_speed=15, initial=12-15
  - Carnivore: max_speed=8, initial=6-8
  - Omnivore: max_speed=12, initial=10-12
- [ ] Replace existing `random.uniform(1.0, 3.0)` logic
- [ ] Use species-specific max_speed in PhysicsComponent creation

**Expected result:** Herbivores move faster than carnivores

---

#### 2.4 Create Unit Tests for Species Stats 🔴
**File:** `server/tests/test_species_stats.py` (new file)
- [ ] Create test: `test_herbivore_has_correct_stats()`
- [ ] Create test: `test_carnivore_has_correct_stats()`
- [ ] Create test: `test_omnivore_has_correct_stats()`
- [ ] Create test: `test_species_stats_differ()`
  - Compare herbivore vs carnivore stats
  - Assert attack, health, energy are different
- [ ] Run: `uv run pytest server/tests/test_species_stats.py -v`

**Expected result:** All tests pass

---

#### 2.5 Test Combat Damage Variation 🔴
**File:** `server/tests/test_species_stats.py`
- [ ] Create test: `test_carnivore_deals_more_damage_than_herbivore()`
  - Create carnivore attacking herbivore
  - Create herbivore attacking carnivore
  - Simulate combat for 1 second
  - Compare damage dealt
- [ ] Run test

**Expected result:** Carnivore deals significantly more damage

---

#### 2.6 Manual Testing in UI 🔴
- [ ] Start simulation with 5 herbivores, 5 carnivores
- [ ] Click on herbivore, verify stats in inspector:
  - Attack: 1, Health: 80, Vision: 70
- [ ] Click on carnivore, verify stats:
  - Attack: 10, Health: 120
- [ ] Observe movement: herbivores should be noticeably faster
- [ ] Watch combat: carnivores should win against herbivores

**Expected result:** Species differentiation visible in UI and behavior

---

#### 2.7 Document Species Stats 🔴
- [ ] Update `docs/phase0-critical-fixes-plan.md` with final stat values (if changed)
- [ ] Add comment in `species.py` explaining stat design philosophy
- [ ] Update PR description with species stat table

**Expected result:** Stats documented for future reference

---

### Success Criteria
- ✅ Herbivores have speed 15, carnivores have speed 8
- ✅ Attack values differ (herbivore 1, carnivore 10)
- ✅ Combat damage varies based on species matchup
- ✅ Stats visible in entity inspector UI
- ✅ Unit tests pass

### Files Modified
- `server/app/simulation/models/species.py`
- `server/app/simulation/factory/component_factory.py`
- `server/tests/test_species_stats.py` (new file)

---

## Fix 3: Implement Basic Reproduction

**Priority:** CRITICAL
**Status:** 🔴 Not Started
**Time Estimate:** 4-5 hours
**Completion:** 0/8 tasks
**Dependencies:** Fix 1 (energy system must be enabled)

### Background
ReproductionComponent exists but is never added to entities. Without reproduction, populations can only decrease, leading to inevitable extinction.

### Tasks

#### 3.1 Complete ReproductionComponent Implementation 🔴
**File:** `server/app/simulation/components/base/reproduction.py`
- [ ] Implement `__init__(self, reproduction_cooldown: float = 10.0)`
- [ ] Implement `update(self, owner, context, dt)` method:
  - Check cooldown timer
  - Check energy threshold
  - Find compatible mate
  - Call _create_offspring if conditions met
- [ ] Implement `_find_compatible_mate()` helper
- [ ] Implement `_create_offspring()` helper
- [ ] Review code in plan document for reference

**Expected result:** Component fully functional

---

#### 3.2 Add Mate Finding Logic 🔴
**File:** `server/app/simulation/components/base/reproduction.py`
- [ ] In `_find_compatible_mate()`:
  - Query nearby entities (20 unit radius)
  - Filter same species
  - Check mate has ReproductionComponent
  - Check mate has energy > threshold
  - Check mate cooldown ready
  - Return first compatible mate or None

**Expected result:** Entities can find compatible mates

---

#### 3.3 Add Offspring Creation Logic 🔴
**File:** `server/app/simulation/components/base/reproduction.py`
- [ ] In `_create_offspring()`:
  - Get parent species from context
  - Calculate spawn position (parent + random 15-unit offset)
  - Clamp to world bounds
  - Create offspring entity via species.create_entity()
  - Register offspring in context
  - Increment species population count

**Expected result:** Offspring spawned correctly

---

#### 3.4 Add Energy Cost and Cooldown Reset 🔴
**File:** `server/app/simulation/components/base/reproduction.py`
- [ ] In `update()` after reproduction:
  - Deduct 40 energy from parent1
  - Deduct 40 energy from parent2 (mate)
  - Reset parent1 cooldown to 0
  - Reset parent2 cooldown to 0

**Expected result:** Parents lose energy and can't reproduce again immediately

---

#### 3.5 Add ReproductionComponent to Entities 🔴
**File:** `server/app/simulation/factory/component_factory.py`
- [ ] Import ReproductionComponent
- [ ] Add to creatures with TWO_PARENTS trait:
  - `entity.add_component(ReproductionComponent(reproduction_cooldown=10.0))`
- [ ] Add to plants with SELF_REPLICATING trait (optional, shorter cooldown):
  - `entity.add_component(ReproductionComponent(reproduction_cooldown=5.0))`

**Expected result:** New entities have reproduction component

---

#### 3.6 Update Simulation Loop 🔴
**File:** `server/app/simulation/simulation.py`
- [ ] In `_update_entities()`, after social component update:
  - Get ReproductionComponent
  - Call reproduction.update(entity, context, dt)

**Expected result:** Reproduction component updates every frame

---

#### 3.7 Create Unit Tests 🔴
**File:** `server/tests/test_reproduction.py` (new file)
- [ ] Create test: `test_reproduction_creates_offspring()`
  - Create 2 entities near each other
  - Set high energy (90) for both
  - Call reproduction.update()
  - Verify offspring created
  - Verify population count increased
- [ ] Create test: `test_reproduction_requires_energy()`
  - Set low energy (50)
  - Try to reproduce
  - Verify no offspring created
- [ ] Create test: `test_reproduction_cooldown()`
  - Reproduce once
  - Immediately try again
  - Verify second attempt fails
  - Wait 10 seconds, try again
  - Verify succeeds
- [ ] Run: `uv run pytest server/tests/test_reproduction.py -v`

**Expected result:** All tests pass

---

#### 3.8 Manual Testing 🔴
- [ ] Start simulation with 10 herbivores
- [ ] Wait for energy bars to reach 75%+
- [ ] Observe population count increasing
- [ ] Click on new offspring, verify it's same species as parents
- [ ] Monitor population over 5 minutes
- [ ] Verify population grows (not just declines)

**Expected result:** Visible population growth via reproduction

---

### Success Criteria
- ✅ Two high-energy entities produce offspring
- ✅ Offspring appears near parents (within 20 units)
- ✅ Parents lose 40 energy each
- ✅ Cooldown prevents continuous reproduction (10 sec)
- ✅ Population count increases over time
- ✅ Unit tests pass

### Files Modified
- `server/app/simulation/components/base/reproduction.py`
- `server/app/simulation/factory/component_factory.py`
- `server/app/simulation/simulation.py`
- `server/tests/test_reproduction.py` (new file)

---

## Fix 4: Fix Plant Spawning

**Priority:** HIGH
**Status:** 🔴 Not Started
**Time Estimate:** 2-3 hours
**Completion:** 0/5 tasks
**Dependencies:** None

### Background
Plants currently spawn at 10% probability per tick (6 plants/sec) with no carrying capacity, leading to either explosion or depletion.

### Tasks

#### 4.1 Implement Carrying Capacity Logic 🔴
**File:** `server/app/simulation/simulation.py`
- [ ] Modify `_spawn_random_plant()` method
- [ ] Add local density check:
  - Query nearby entities in 30-unit radius
  - Count existing plants
  - If count >= 5, return early (don't spawn)
- [ ] Keep random position generation
- [ ] Keep spawn logic (only if density check passes)

**Expected result:** Plants don't spawn in dense areas

---

#### 4.2 Reduce Plant Spawn Rate 🔴
**File:** `server/app/simulation/simulation.py`
- [ ] In simulation loop, find plant spawn probability check
- [ ] Change from `if random.random() < 0.1:` to `if random.random() < 0.05:`
- [ ] Add comment explaining: "3 spawn attempts/sec instead of 6"

**Expected result:** Fewer spawn attempts per second

---

#### 4.3 Test Carrying Capacity 🔴
**File:** `server/tests/test_plant_spawning.py` (new file)
- [ ] Create test: `test_plant_carrying_capacity()`
  - Spawn 5 plants in 30-unit radius around position
  - Try to spawn 100 more plants at same position
  - Verify very few (0-2) additional plants spawned
- [ ] Run test

**Expected result:** Test passes, confirming carrying capacity works

---

#### 4.4 Test Population Stabilization 🔴
**File:** `server/tests/test_plant_spawning.py`
- [ ] Create test: `test_plant_population_stabilizes()`
  - Run simulation for 2 minutes
  - Record plant count every second
  - Check last 10 readings have low variance
  - Check average is 100-300 plants
- [ ] Run test (may be slow, ~2 min runtime)

**Expected result:** Plant population stabilizes

---

#### 4.5 Manual Testing 🔴
- [ ] Start simulation with 50 plants
- [ ] Let run for 5 minutes
- [ ] Record plant count every 30 seconds:
  - 0:00 - 50
  - 0:30 - ???
  - 1:00 - ???
  - 1:30 - ???
  - 2:00 - ???
  - ... (continue to 5:00)
- [ ] Verify count stabilizes in range 100-250
- [ ] Add 50 herbivores
- [ ] Verify plants still regrow (don't crash to 0)

**Expected result:** Stable plant population even with consumption

---

### Success Criteria
- ✅ Plant population stabilizes (not exponential growth)
- ✅ Target range: 100-250 plants
- ✅ Dense areas don't spawn more plants
- ✅ Depleted areas regrow over time
- ✅ Unit tests pass

### Files Modified
- `server/app/simulation/simulation.py`
- `server/tests/test_plant_spawning.py` (new file)

---

## Fix 5: Balance Energy Economy

**Priority:** HIGH
**Status:** 🔴 Not Started
**Time Estimate:** 3-4 hours
**Completion:** 0/6 tasks
**Dependencies:** Fix 1 (energy enabled), Fix 4 (plant spawning stable)

### Background
Energy values were set when energy decay was disabled. Now that decay is enabled, food values may not sustain populations.

### Tasks

#### 5.1 Update Food Energy Values 🔴
**File:** `server/app/simulation/components/base/diet.py`
- [ ] Find PLANT_ENERGY_VALUE definition (around line 40-50)
- [ ] Change from `15` to `25`
- [ ] Find MEAT_ENERGY_VALUE definition
- [ ] Change from `30` to `60`
- [ ] Find HUNGER_REDUCTION definition
- [ ] Change from `50` to `30`
- [ ] Add comments explaining values

**Expected result:** Eating provides more energy

---

#### 5.2 Test Herbivore Survival Time 🔴
**File:** `server/tests/test_energy_balance.py` (new file)
- [ ] Create test: `test_herbivore_survival_time()`
  - Spawn herbivore with 10 nearby plants
  - Simulate until death or 120 seconds
  - Verify survival time >= 30 seconds
  - Print actual survival time for tuning
- [ ] Run test

**Expected result:** Herbivores survive 30-60 seconds with food

---

#### 5.3 Test Carnivore Can Sustain on Prey 🔴
**File:** `server/tests/test_energy_balance.py`
- [ ] Create test: `test_carnivore_sustains_on_prey()`
  - Spawn carnivore with 5 herbivores nearby
  - Simulate for 60 seconds
  - Verify carnivore still alive
  - Verify carnivore killed at least 1 herbivore
- [ ] Run test

**Expected result:** Carnivores can survive by hunting

---

#### 5.4 Balance Tuning Iteration 1 🔴
- [ ] Run 5-minute simulation with balanced ecosystem:
  - 50 plants
  - 20 herbivores
  - 8 carnivores
- [ ] Observe populations:
  - If herbivores die too fast: increase PLANT_ENERGY_VALUE by 5
  - If herbivores never die: decrease to 20
  - If carnivores die too fast: increase MEAT_ENERGY_VALUE by 10
  - If carnivores dominate: decrease to 50
- [ ] Document observations

**Expected result:** Identify needed adjustments

---

#### 5.5 Balance Tuning Iteration 2 🔴
- [ ] Apply adjustments from iteration 1
- [ ] Run another 5-minute simulation
- [ ] Target outcomes:
  - Herbivore population: 15-30 (stable or slowly growing)
  - Carnivore population: 5-12 (stable)
  - Plant population: 100-200 (stable)
- [ ] If not in ranges, adjust again
- [ ] Document final values in PR

**Expected result:** All populations stable

---

#### 5.6 Integration Test for Ecosystem Sustainability 🔴
**File:** `server/tests/test_energy_balance.py`
- [ ] Create test: `test_ecosystem_sustainability()`
  - Create balanced ecosystem
  - Run for 5 minutes (300 seconds)
  - Verify all species still alive at end
  - Verify minimum populations: plants > 20, herbivores > 5, carnivores > 2
- [ ] Run test (slow, ~5 min)

**Expected result:** Test passes, ecosystem survives

---

### Success Criteria
- ✅ Herbivores survive 30-60 seconds average with food
- ✅ Carnivores can sustain on prey
- ✅ Both populations survive 5+ minutes
- ✅ Energy bars fluctuate (not always full/empty)
- ✅ Integration tests pass

### Files Modified
- `server/app/simulation/components/base/diet.py`
- `server/app/simulation/core/config.py` (if decay rate adjusted)
- `server/tests/test_energy_balance.py` (new file)

---

## Fix 6: Add Flee Behavior

**Priority:** HIGH
**Status:** 🔴 Not Started
**Time Estimate:** 2-3 hours
**Completion:** 0/5 tasks
**Dependencies:** Fix 2 (species speed differences)

### Background
Prey species don't flee from predators, making hunting trivial and leading to rapid herbivore extinction.

### Tasks

#### 6.1 Add Threat Detection to PhysicsComponent 🔴
**File:** `server/app/simulation/components/base/physics.py`
- [ ] Add method: `_detect_nearby_threat(owner, context) -> Optional[Entity]`
  - Only trigger for herbivores
  - Check if entity is vulnerable (health < 50% or energy < 30%)
  - Query nearby entities (use entity vision range)
  - Filter for carnivores/omnivores
  - Return nearest threat or None
- [ ] Add import for Trait enum

**Expected result:** Method identifies nearby predators

---

#### 6.2 Implement Flee Logic 🔴
**File:** `server/app/simulation/components/base/physics.py`
- [ ] In `update()` method, before wander behavior:
  - Call `threat = self._detect_nearby_threat(owner, context)`
  - If threat exists:
    - Calculate flee_direction (owner.position - threat.position).normalized()
    - Set flee_force = flee_direction × max_force × 2.0
    - Apply flee force to velocity
    - Skip normal movement behaviors (early return)
- [ ] Ensure flee has highest priority (before food seeking, wandering)

**Expected result:** Herbivores flee when predators approach

---

#### 6.3 Test Flee Detection 🔴
**File:** `server/tests/test_flee_behavior.py` (new file)
- [ ] Create test: `test_herbivore_detects_nearby_carnivore()`
  - Spawn herbivore and carnivore 25 units apart
  - Call _detect_nearby_threat()
  - Verify threat detected (returns carnivore)
- [ ] Create test: `test_herbivore_ignores_distant_carnivore()`
  - Spawn herbivore and carnivore 100 units apart
  - Call _detect_nearby_threat()
  - Verify no threat detected (returns None)
- [ ] Run tests

**Expected result:** Threat detection works correctly

---

#### 6.4 Test Flee Direction 🔴
**File:** `server/tests/test_flee_behavior.py`
- [ ] Create test: `test_flee_direction_is_away_from_threat()`
  - Spawn herbivore at (100, 100)
  - Spawn carnivore at (120, 100) (to the right)
  - Update physics for herbivore
  - Verify herbivore velocity points left (negative X)
- [ ] Run test

**Expected result:** Herbivore flees in opposite direction from threat

---

#### 6.5 Manual Testing and Tuning 🔴
- [ ] Start simulation with 10 herbivores, 5 carnivores
- [ ] Observe chases:
  - Herbivores should flee when carnivores within ~30 units
  - Some herbivores should escape
  - Some herbivores should get caught
- [ ] Target: ~50% escape rate
- [ ] If escape rate too high (>70%):
  - Reduce flee force multiplier from 2.0 to 1.5
  - Or reduce herbivore speed from 15 to 13
- [ ] If escape rate too low (<30%):
  - Increase flee activation distance
  - Or increase herbivore speed to 17
- [ ] Document final parameters in PR

**Expected result:** Balanced predator-prey chases

---

### Success Criteria
- ✅ Herbivores flee when carnivores approach (<30 units)
- ✅ Flee direction is away from predator
- ✅ Flee speed equals max speed (15 for herbivores)
- ✅ Some prey escape, some get caught (50/50 balance)
- ✅ Unit tests pass

### Files Modified
- `server/app/simulation/components/base/physics.py`
- `server/tests/test_flee_behavior.py` (new file)

---

## Overall Testing & Validation

**Status:** 🔴 Not Started
**Time Estimate:** 4-6 hours

### Integration Testing

#### Full Ecosystem Survival Test 🔴
**File:** `server/tests/test_phase0_integration.py` (new file)
- [ ] Create test: `test_full_ecosystem_survives_10_minutes()`
  - Create balanced ecosystem (50 plants, 20 herbivores, 8 carnivores)
  - Run for 10 minutes (600 seconds)
  - Verify all species still alive
  - Verify minimum populations maintained
- [ ] Run test (slow, 10+ min with simulation)

---

#### Population Dynamics Test 🔴
**File:** `server/tests/test_phase0_integration.py`
- [ ] Create test: `test_predator_prey_dynamics()`
  - Track populations over 10 minutes
  - Record every 10 seconds
  - Verify populations fluctuate (boom/bust cycles)
  - Check herbivore max > 2× herbivore min
- [ ] Run test

---

### Performance Testing

#### 500 Entity Performance Test 🔴
**File:** `server/tests/test_performance.py` (may already exist)
- [ ] Create test: `test_500_entity_maintains_60fps()`
  - Spawn 500 entities (mix of species)
  - Measure 100 frame update times
  - Calculate average frame time
  - Verify average < 16ms (60 FPS)
- [ ] Run test

---

### Manual Testing Scenarios

#### Scenario 1: Energy System Verification 🔴
- [ ] Start fresh simulation
- [ ] Observe energy bars decreasing
- [ ] Observe creatures seeking food
- [ ] Observe creatures dying from starvation
- [ ] Observe energy restoring after eating
- [ ] Document with screenshots/video if possible

---

#### Scenario 2: Species Differentiation 🔴
- [ ] Spawn 1 herbivore, 1 carnivore side by side
- [ ] Observe herbivore moves faster
- [ ] Watch combat: carnivore should win
- [ ] Check stats in UI inspector
- [ ] Verify different values displayed

---

#### Scenario 3: Reproduction 🔴
- [ ] Start with 10 herbivores
- [ ] Wait for energy > 75%
- [ ] Observe offspring appearing
- [ ] Verify population count increases
- [ ] Monitor for 5 minutes
- [ ] Verify sustained growth

---

#### Scenario 4: Plant Population Stability 🔴
- [ ] Start with 50 plants
- [ ] Record counts every minute for 5 minutes
- [ ] Plot counts: should stabilize around 150-200
- [ ] Add 50 herbivores
- [ ] Verify plants still regrow

---

#### Scenario 5: Flee Behavior 🔴
- [ ] Spawn 1 herbivore, 1 carnivore
- [ ] Move carnivore toward herbivore
- [ ] Verify herbivore flees
- [ ] Lower herbivore health to 30%
- [ ] Verify herbivore flees from further away

---

#### Scenario 6: Long-Running Stability 🔴
- [ ] Start balanced ecosystem
- [ ] Let run for 30 minutes unattended
- [ ] Check for:
  - No crashes or errors
  - All species still alive
  - Reasonable populations
  - No performance degradation
- [ ] Document results

---

## Known Issues & Blockers

### Current Blockers
None (ready to start implementation)

### Potential Issues

#### Energy Balance May Need Multiple Iterations ⚠️
**Risk:** Food values may need tuning multiple times to get right balance
**Mitigation:** Budget extra time for Fix 5, use automated tests to speed iteration
**Owner:** Assigned developer

---

#### Flee Behavior May Feel "Twitchy" ⚠️
**Risk:** Constant fleeing might make simulation feel chaotic
**Mitigation:** Add "safe distance" - stop fleeing when far enough away
**Status:** Monitor during testing

---

#### Reproduction May Cause Population Explosion 🔴
**Risk:** Too many offspring → simulation slows down
**Mitigation:**
- Cooldown timer (10 sec) limits reproduction rate
- Energy cost (40) prevents continuous reproduction
- Max entity limit (add if needed)
**Status:** Not started

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Frame time (500 entities) | <12ms | <16ms | <20ms |
| Energy calculation | <0.001ms/entity | <0.005ms | <0.01ms |
| Memory usage | <100MB | <200MB | <500MB |
| Test suite runtime | <30 sec | <60 sec | <120 sec |

### Benchmark After Each Fix

- [ ] After Fix 1: Measure energy calculation time
- [ ] After Fix 2: Measure with different stat entities
- [ ] After Fix 3: Measure with reproduction active
- [ ] After Fix 4: Measure plant spawn overhead
- [ ] After Fix 5: Full ecosystem benchmark
- [ ] After Fix 6: Measure flee detection overhead

---

## Timeline & Schedule

### Recommended Schedule

**Day 1 (8 hours):**
- 9:00-10:30: Fix 1 - Energy system (1.5h)
- 10:30-12:00: Fix 1 - Testing & tuning (1.5h)
- 12:00-13:00: Lunch break
- 13:00-16:00: Fix 2 - Species stats (3h)
- 16:00-17:00: Fix 2 - Testing

**Day 2 (8 hours):**
- 9:00-11:00: Fix 3 - Reproduction implementation (2h)
- 11:00-13:00: Fix 3 - Testing & debugging (2h)
- 13:00-14:00: Lunch break
- 14:00-16:00: Fix 4 - Plant spawning (2h)
- 16:00-17:00: Fix 4 - Testing

**Day 3 (8 hours):**
- 9:00-12:00: Fix 5 - Energy balance tuning (3h, may need multiple iterations)
- 12:00-13:00: Lunch break
- 13:00-15:00: Fix 6 - Flee behavior (2h)
- 15:00-17:00: Integration testing & bug fixes

**Buffer Time:**
- Add extra 0.5 days if needed for challenging fixes
- Prioritize Fixes 1-3 (critical for functionality)
- Fixes 4-6 can be deferred if time-constrained

---

## Definition of Done

### Phase 0 is complete when:

- [ ] All 6 fixes implemented and committed
- [ ] All unit tests passing (37+ tests total)
- [ ] Integration tests passing
- [ ] Performance benchmarks met (60 FPS with 500 entities)
- [ ] All manual testing scenarios completed
- [ ] Documentation updated
- [ ] PR created and reviewed
- [ ] Changes merged to main branch
- [ ] Deployed to staging environment
- [ ] Validated on staging (30-minute run without issues)

### Ready for Phase 1 when:

- [ ] Phase 0 DOD complete
- [ ] No critical bugs in issue tracker
- [ ] Ecosystem survives 30+ minutes consistently
- [ ] All species populations remain stable
- [ ] Team sign-off received

---

## Quick Commands Reference

### Run Specific Test Files
```bash
# Energy/Vitality tests
uv run pytest server/tests/test_vitality.py -v

# Species stats tests
uv run pytest server/tests/test_species_stats.py -v

# Reproduction tests
uv run pytest server/tests/test_reproduction.py -v

# Plant spawning tests
uv run pytest server/tests/test_plant_spawning.py -v

# Energy balance tests
uv run pytest server/tests/test_energy_balance.py -v

# Flee behavior tests
uv run pytest server/tests/test_flee_behavior.py -v

# Integration tests
uv run pytest server/tests/test_phase0_integration.py -v

# Run all Phase 0 tests
uv run pytest server/tests/test_*.py -v

# Run with coverage
uv run pytest server/tests/ --cov=app --cov-report=html
```

### Start Simulation
```bash
# Backend
cd server
uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd client
npm run dev

# Or use dev script
./scripts/dev-native.sh
```

---

## Notes & Observations

### Implementation Notes
(Add notes during implementation)

---

### Issues Encountered
(Document any issues found during implementation)

---

### Deviations from Plan
(Record any changes from original plan)

---

## Links & References

- **Implementation Plan:** [phase0-critical-fixes-plan.md](./phase0-critical-fixes-plan.md)
- **Backend Resilience:** [backend-resilience-plan.md](./backend-resilience-plan.md)
- **Genetic Evolution Plan:** [genetic-evolution-plan.md](./genetic-evolution-plan.md)
- **Development Guide:** [DEVELOPMENT.md](./DEVELOPMENT.md)

---

**Document Owner:** Development Team
**Last Updated:** 2025-10-18
**Next Review:** After each fix completion
