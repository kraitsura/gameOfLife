# Genetic Evolution Integration Plan

**Version:** 1.0
**Date:** 2025-10-18
**Status:** Planning Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current System Analysis](#current-system-analysis)
3. [Reference System Analysis](#reference-system-analysis)
4. [Integration Architecture](#integration-architecture)
5. [Technical Specifications](#technical-specifications)
6. [Implementation Phases](#implementation-phases)
7. [Performance Analysis](#performance-analysis)
8. [API and Data Structure Changes](#api-and-data-structure-changes)
9. [Testing Strategy](#testing-strategy)
10. [Future Enhancements](#future-enhancements)

---

## Executive Summary

### Vision
Transform the current multi-species particle simulation into a **genetic evolution ecosystem** where species evolve through natural selection, creatures develop emergent behaviors via neural networks, and users can create custom species that adapt over time.

### Core Goals
1. **Enable true evolution**: Species adapt through genetic inheritance and mutation
2. **Create emergent behavior**: Replace hardcoded behaviors with evolved neural networks
3. **Support user creativity**: Let users design custom species that evolve unique strategies
4. **Maintain performance**: Keep real-time 60 FPS WebSocket updates for web clients
5. **Preserve ecosystem dynamics**: Multi-species predator-prey interactions remain core feature

### Key Features to Add
- **Genome system**: Heritable genetic code encoding stats and neural networks
- **Sexual reproduction**: Gene crossover and mutation between parents
- **Neural network brains**: Creatures make decisions via evolved networks (5 inputs, 1-2 hidden, 4 outputs)
- **Natural selection**: Successful traits spread through population via survival and reproduction
- **Species gene pools**: Each species maintains population-wide genetic diversity
- **User species creation**: UI for designing species with evolvable traits

### Success Metrics
- Populations show evolutionary adaptation over 100+ generations
- Emergent behaviors arise that weren't explicitly programmed
- Ecosystem remains balanced without extinction for 30+ minute sessions
- User-created species successfully compete in the ecosystem
- Real-time performance maintained at 60 FPS with 500+ entities

---

## Current System Analysis

### Architecture Overview
The simulation uses an **Entity-Component System (ECS)** architecture:
- **Entities**: Creatures and plants with unique IDs
- **Components**: Modular behaviors (Physics, Vitality, Diet, Social, Reproduction)
- **Species**: Templates that define base traits
- **Packs**: Groups of entities that coordinate
- **SimulationContext**: Dependency injection container and spatial queries

### Current Flow
```
Client (React + Canvas)
    ↕ WebSocket (60 FPS)
Backend (FastAPI + Python)
    ↓
SimulationManager (main loop)
    ↓
Entity Updates (Physics → Vitality → Diet → Social)
    ↓
Broadcast State (entities, species, packs)
```

### Critical Issues Identified

#### 1. Energy and Hunger System is DISABLED ⚠️
**Location:** `server/app/simulation/core/config.py:24-25`
```python
VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.0,  # DISABLED
    "HUNGER_RATE": 0.0,        # DISABLED
    "REPRODUCTION_THRESHOLD": 90.0
}
```
**Impact:** Creatures never need to eat, no survival pressure, no predator-prey dynamics
**Fix Required:** Re-enable with balanced rates before genetic evolution will work

#### 2. All Species Have Identical Stats ⚠️
**Location:** `server/app/simulation/models/entity.py:28-41`
```python
@dataclass
class EntityStats:
    max_health: float = 100.0
    defense: float = 0.0      # All creatures: 0
    attack: float = 0.0        # All creatures: 0
    max_energy: float = 100.0
    entity_vision: float = 50.0
```
**Impact:** No species differentiation, combat is uniform, no evolutionary pressure for stat optimization
**Fix Required:** Species-specific stat initialization

#### 3. Reproduction System Not Implemented ❌
**Location:** `server/app/simulation/factory/component_factory.py:52`
```python
# Line 52: "TODO: Add ReproductionComponent in future phases"
```
**Impact:** Populations only decrease, eventual extinction guaranteed, no genetic inheritance possible
**Fix Required:** Implement ReproductionComponent before genetic evolution

#### 4. Plant Respawn is Too Simplistic
**Location:** `server/app/simulation/simulation.py:62-64`
```python
if random.random() < 0.1:  # 10% per tick = ~6 plants/second
    self._spawn_random_plant()
```
**Impact:** No carrying capacity, resource availability unpredictable
**Fix Required:** Density-based spawning with local limits

### Current Component Functionality

#### PhysicsComponent (`physics.py`)
- Steering behaviors: seek, flee, wander, separation, cohesion, alignment
- Boid-like flocking with same-species interactions
- Wall bouncing with 20% energy loss
- **Works well**: Good foundation for movement

#### VitalityComponent (`vitality.py`)
- Health (max 100), energy (max 100), hunger, age tracking
- Death conditions: health = 0, hunger > threshold, energy = 0
- **Broken**: Energy decay and hunger disabled
- **Needs**: Integration with reproduction system

#### DietComponent (`diet.py`)
- Food seeking with vision range (50 units)
- Spatial grid queries for efficient lookup
- Combat system with damage-over-time
- Energy gain: Plants +15, Meat +30
- **Needs**: Balance tuning when energy re-enabled
- **Opportunity**: Replace with neural network decisions

#### SocialComponent (`social.py`)
- Pack formation (stay within 30 units for 5 seconds)
- Relationship tracking
- **Minimal benefits**: Only combat damage multiplier
- **Opportunity**: Pack hunting strategies via neural networks

#### ReproductionComponent (`reproduction.py`)
- **Status**: Stub implementation, not used
- **Designed for**: Maturity age, cooldown, pregnancy
- **Needs**: Complete implementation with genetic crossover

### What Works Well
✅ ECS architecture is clean and extensible
✅ WebSocket communication is reliable
✅ Spatial grid queries are efficient
✅ Physics system supports diverse movement
✅ Frontend rendering is smooth

### What Needs Fixing Before Evolution
🔴 Re-enable energy/hunger system
🔴 Differentiate species stats
🔴 Implement reproduction with inheritance
🔴 Balance resource economy
🔴 Add flee behavior for prey

---

## Reference System Analysis

### Overview
The reference genetic evolution simulation (similar to biosim4) demonstrates:
- **Genomes as hexadecimal strings** encoding neural network connections
- **32-bit genes** defining source neuron → sink neuron connections with weights
- **Sexual reproduction** with genome crossover and mutation
- **Discrete generations** with selection culling between generations
- **C++ performance** with OpenMP parallelization for thousands of creatures

### Key Concepts to Adopt

#### 1. Genome as Neural Network Blueprint
```
Gene (32 bits):
- Source Type (1 bit): Input (0) or Internal (1)
- Source ID (7 bits): Which neuron
- Sink Type (1 bit): Internal (0) or Output (1)
- Sink ID (7 bits): Which neuron
- Weight (16 bits): Connection strength (-32k to +32k)

Genome = List[Gene] → Neural Network
```
**Why adopt:** Deterministic, heritable, evolvable network structure

#### 2. Sensory Input Neurons
Reference system includes:
- Position sensors (X, Y)
- Genetic similarity (recognize kin)
- Border proximity
- Pheromone sensors
- Population density
- Age sensor
- Oscillator (rhythmic behavior)

**What we'll use:**
- Hunger level (0-1)
- Food direction (X, Y)
- Threat distance (0-1)
- Current energy (0-1)
- Age (0-1)

#### 3. Action Output Neurons
Reference system includes:
- Move X, Move Y
- Move forward
- Move random
- Emit pheromone
- Responsiveness level

**What we'll use:**
- Move X (-1 to 1)
- Move Y (-1 to 1)
- Attack probability (0-1)
- Reproduce probability (0-1)

#### 4. Mutation System
- Mutation rate: 1/1000 per gene (reference)
- Mutation type: Single bit flips
- Creates variation for natural selection

**Our adaptation:** 1/100 per gene for faster observable evolution

#### 5. Sexual Reproduction
```python
child_genome = []
for gene_idx in range(genome_length):
    if random.random() < 0.5:
        child_genome.append(parent1.genome[gene_idx])
    else:
        child_genome.append(parent2.genome[gene_idx])

    # Mutation
    if random.random() < mutation_rate:
        child_genome[-1] = mutate(child_genome[-1])
```

### Key Differences from Reference System

| Aspect | Reference System | Our System |
|--------|-----------------|------------|
| Movement | Discrete grid, 8 directions | Continuous 2D physics |
| Generations | Discrete with culling | Continuous with rolling births/deaths |
| Species | Single evolving population | Multi-species ecosystem |
| Selection | Manual (spatial zones, etc.) | Natural (predation, starvation) |
| Platform | C++ desktop simulation | Python backend + web frontend |
| Performance | OpenMP parallelization | Real-time 60 FPS constraint |
| Network Size | Large (hundreds of connections) | Small (20-40 connections) |

### What We CANNOT Use
❌ Grid-based movement (we have continuous physics)
❌ Generational structure (we're real-time)
❌ Single population (we're multi-species)
❌ Desktop C++ performance model (we're web-based)
❌ Large neural networks (performance constraint)

### What We WILL Use
✅ Genome encoding neural networks
✅ Sexual reproduction with crossover
✅ Mutation system
✅ Gene-defined connection weights
✅ Sensory input → internal → action output architecture
✅ Evolution through natural selection

---

## Integration Architecture

### Hybrid Design Philosophy
Combine the best of both systems:
- **From reference:** Genetic algorithms, neural network genomes, evolution
- **From current:** Multi-species ecosystem, continuous physics, real-time web

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  - Canvas rendering (60 FPS)                                │
│  - Species creation UI (trait sliders → genome templates)   │
│  - Evolution visualization (gene pool diversity graphs)     │
└─────────────────────┬───────────────────────────────────────┘
                      │ WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                Backend (FastAPI + Python)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           SimulationManager (60 FPS Loop)            │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼──────────────────────────────────────────────────┐ │
│  │              Entity Update Pipeline                    │ │
│  │  1. Neural Network Brain (NEW)                        │ │
│  │     - Process sensory inputs                          │ │
│  │     - Compute internal neuron activations            │ │
│  │     - Output action decisions                         │ │
│  │  2. Physics Component                                 │ │
│  │  3. Vitality Component                                │ │
│  │  4. Diet Component (uses neural decisions)            │ │
│  │  5. Social Component                                  │ │
│  │  6. Reproduction Component (NEW - genetic crossover)  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Species Gene Pool (NEW)                   │ │
│  │  - Population-wide genome statistics                  │ │
│  │  - Allele frequencies                                 │ │
│  │  - Evolutionary trends tracking                       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow with Genetics
```
1. Species Created (by user or default)
   ↓
2. Generate Base Genome Template
   - Encode initial trait values as genes
   - Create neural network structure
   ↓
3. Spawn Initial Population
   - Each entity gets genome with slight variation
   ↓
4. Simulation Loop (60 FPS)
   For each entity:
     a. Neural Network processes inputs → decisions
     b. Actions executed (movement, attack, etc.)
     c. Energy consumed, damage taken
     d. Check reproduction conditions
   ↓
5. Reproduction Event (when energy > threshold + mate found)
   a. Sexual crossover: 50% genes from each parent
   b. Mutation: 1/100 chance per gene
   c. Child spawned with new genome
   d. Species gene pool updated
   ↓
6. Natural Selection
   - Weak/hungry creatures die
   - Successful hunters survive
   - Good genes spread through population
   ↓
7. Evolution Over Time
   - Species adapts to environment
   - Emergent behaviors develop
   - Gene pool shifts toward successful strategies
```

### Component Integration

#### Existing Components (Modified)
```python
# PhysicsComponent - uses neural network outputs
class PhysicsComponent:
    def update(self, owner, context, dt):
        # Get movement decision from neural network
        brain = owner.get_component('NeuralBrainComponent')
        if brain:
            move_x, move_y = brain.get_movement_output()
            self.velocity = Vector2D(move_x, move_y) * self.max_speed
        else:
            # Fallback to old wander behavior
            self.velocity = self._wander()
```

```python
# DietComponent - uses neural network attack decision
class DietComponent:
    def update(self, owner, context, dt):
        brain = owner.get_component('NeuralBrainComponent')
        if brain:
            should_attack = brain.get_attack_output() > 0.5
            if should_attack:
                self._attack_nearest_prey(owner, context, dt)
        else:
            # Fallback to old behavior
            self._seek_food_automatically(owner, context, dt)
```

#### New Components

```python
# NeuralBrainComponent - decision-making via evolved network
class NeuralBrainComponent(Component):
    def __init__(self, genome: Genome):
        self.genome = genome
        self.network = self._build_network_from_genome(genome)
        self.internal_state = {}  # For recurrent connections

    def update(self, owner, context, dt):
        # Gather sensory inputs
        inputs = self._get_sensory_inputs(owner, context)

        # Process through neural network
        outputs = self.network.forward(inputs, self.internal_state)

        # Store outputs for other components to use
        self.last_outputs = outputs

    def get_movement_output(self) -> Tuple[float, float]:
        return (self.last_outputs['move_x'], self.last_outputs['move_y'])

    def get_attack_output(self) -> float:
        return self.last_outputs['attack_probability']

    def get_reproduce_output(self) -> float:
        return self.last_outputs['reproduce_probability']
```

```python
# ReproductionComponent - genetic crossover and mutation
class ReproductionComponent(Component):
    def __init__(self, cooldown: float = 10.0, mutation_rate: float = 0.01):
        self.cooldown = cooldown
        self.time_since_last = cooldown
        self.mutation_rate = mutation_rate

    def update(self, owner, context, dt):
        self.time_since_last += dt

        # Check if ready and willing to reproduce
        vitality = owner.get_component('VitalityComponent')
        brain = owner.get_component('NeuralBrainComponent')

        if (self.time_since_last >= self.cooldown and
            vitality.current_energy >= REPRODUCTION_THRESHOLD and
            brain.get_reproduce_output() > 0.7):  # Neural decision

            mate = self._find_compatible_mate(owner, context)
            if mate:
                self._reproduce(owner, mate, context)
                self.time_since_last = 0.0

    def _reproduce(self, parent1, parent2, context):
        # Genetic crossover
        genome1 = parent1.get_component('NeuralBrainComponent').genome
        genome2 = parent2.get_component('NeuralBrainComponent').genome

        child_genome = self._crossover(genome1, genome2)
        child_genome = self._mutate(child_genome)

        # Spawn offspring
        spawn_pos = parent1.position + random_offset(15)
        child = self._create_child_entity(child_genome, spawn_pos, parent1.species_id)
        context.register(child)

        # Energy cost
        parent1.get_component('VitalityComponent').current_energy -= 40
        parent2.get_component('VitalityComponent').current_energy -= 40
```

```python
# SpeciesGenePoolComponent - tracks population genetics
class SpeciesGenePoolComponent(Component):
    """Attached to Species entities to track genetic diversity"""
    def __init__(self):
        self.population_genomes: List[Genome] = []
        self.allele_frequencies: Dict[int, Dict[str, float]] = {}
        self.generation_count: int = 0
        self.average_fitness: float = 0.0

    def update(self, owner, context, dt):
        # Periodically recalculate gene pool statistics
        if context.current_tick % 300 == 0:  # Every 5 seconds
            self._update_statistics(context)

    def record_birth(self, genome: Genome):
        """Called when new entity is born"""
        self.population_genomes.append(genome)
        self.generation_count += 1

    def record_death(self, genome: Genome):
        """Called when entity dies"""
        if genome in self.population_genomes:
            self.population_genomes.remove(genome)
```

### Neural Network Architecture

#### Simplified Design for Web Performance
```
INPUT LAYER (5 neurons):
  1. hunger_level (0-1)
  2. nearest_food_direction_x (-1 to 1)
  3. nearest_food_direction_y (-1 to 1)
  4. nearest_threat_distance (0-1, normalized)
  5. current_energy_ratio (0-1)

INTERNAL LAYER (1-2 neurons):
  - Hidden neurons for complex decision-making
  - Can connect to each other (recurrent)

OUTPUT LAYER (4 neurons):
  1. move_x (-1 to 1)
  2. move_y (-1 to 1)
  3. attack_probability (0-1)
  4. reproduce_probability (0-1)

Total connections: 5 inputs × 2 internal + 2 internal × 4 outputs + 2 recurrent
                 = 10 + 8 + 2 = 20 connections
```

#### Computation Model
```python
class SimpleNeuralNetwork:
    def forward(self, inputs: Dict[str, float], state: Dict[int, float]) -> Dict[str, float]:
        # Step 1: Activate internal neurons
        internal_outputs = {}
        for neuron_id in self.internal_neurons:
            weighted_sum = 0.0

            # Input → Internal connections
            for input_name, input_value in inputs.items():
                if (input_name, neuron_id) in self.connections:
                    weight = self.connections[(input_name, neuron_id)]
                    weighted_sum += input_value * weight

            # Internal → Internal (recurrent)
            for other_id, other_value in state.items():
                if (other_id, neuron_id) in self.connections:
                    weight = self.connections[(other_id, neuron_id)]
                    weighted_sum += other_value * weight

            # Activation function: tanh
            internal_outputs[neuron_id] = math.tanh(weighted_sum)

        # Step 2: Activate output neurons
        outputs = {}
        for output_name in ['move_x', 'move_y', 'attack_probability', 'reproduce_probability']:
            weighted_sum = 0.0

            # Input → Output (direct connections)
            for input_name, input_value in inputs.items():
                if (input_name, output_name) in self.connections:
                    weight = self.connections[(input_name, output_name)]
                    weighted_sum += input_value * weight

            # Internal → Output
            for internal_id, internal_value in internal_outputs.items():
                if (internal_id, output_name) in self.connections:
                    weight = self.connections[(internal_id, output_name)]
                    weighted_sum += internal_value * weight

            # Activation: tanh for movement, sigmoid for probabilities
            if 'move' in output_name:
                outputs[output_name] = math.tanh(weighted_sum)
            else:
                outputs[output_name] = 1.0 / (1.0 + math.exp(-weighted_sum))

        # Update recurrent state
        state.update(internal_outputs)

        return outputs
```

---

## Technical Specifications

### Genome Data Structure

```python
from dataclasses import dataclass
from typing import List, Literal

@dataclass
class Gene:
    """Single gene encoding one neural connection"""
    source_type: Literal['input', 'internal']
    source_id: int  # Index in input or internal neuron list
    sink_type: Literal['internal', 'output']
    sink_id: int    # Index in internal or output neuron list
    weight: float   # Connection strength, typically -4.0 to +4.0

    def to_bytes(self) -> bytes:
        """Encode gene as 32 bits for storage/transmission"""
        source_type_bit = 0 if self.source_type == 'input' else 1
        source_id_bits = self.source_id & 0x7F  # 7 bits
        sink_type_bit = 0 if self.sink_type == 'internal' else 1
        sink_id_bits = self.sink_id & 0x7F  # 7 bits
        weight_bits = int((self.weight / 8.0) * 32768) & 0xFFFF  # 16 bits signed

        value = (source_type_bit << 31 | source_id_bits << 24 |
                 sink_type_bit << 23 | sink_id_bits << 16 | weight_bits)
        return value.to_bytes(4, byteorder='big')

    @staticmethod
    def from_bytes(data: bytes) -> 'Gene':
        """Decode gene from 32 bits"""
        value = int.from_bytes(data, byteorder='big')
        source_type = 'internal' if (value >> 31) & 1 else 'input'
        source_id = (value >> 24) & 0x7F
        sink_type = 'output' if (value >> 23) & 1 else 'internal'
        sink_id = (value >> 16) & 0x7F
        weight_raw = value & 0xFFFF
        # Convert unsigned to signed
        weight = ((weight_raw - 32768) if weight_raw >= 32768 else weight_raw) / 32768.0 * 8.0

        return Gene(source_type, source_id, sink_type, sink_id, weight)

@dataclass
class Genome:
    """Complete genetic code for one entity"""
    genes: List[Gene]
    metadata: Dict[str, Any] = None  # Species ID, generation, parent IDs, etc.

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_hex_string(self) -> str:
        """Convert genome to hexadecimal string (like reference system)"""
        return ''.join(gene.to_bytes().hex() for gene in self.genes)

    @staticmethod
    def from_hex_string(hex_str: str) -> 'Genome':
        """Parse genome from hexadecimal string"""
        genes = []
        for i in range(0, len(hex_str), 8):
            gene_hex = hex_str[i:i+8]
            gene_bytes = bytes.fromhex(gene_hex)
            genes.append(Gene.from_bytes(gene_bytes))
        return Genome(genes)

    def copy(self) -> 'Genome':
        """Deep copy of genome"""
        return Genome(
            genes=[Gene(g.source_type, g.source_id, g.sink_type, g.sink_id, g.weight)
                   for g in self.genes],
            metadata=self.metadata.copy()
        )
```

### Genetic Operators

```python
class GeneticOperators:
    """Functions for reproduction and evolution"""

    @staticmethod
    def crossover(parent1_genome: Genome, parent2_genome: Genome) -> Genome:
        """Sexual reproduction: mix genes from two parents"""
        child_genes = []
        genome_length = len(parent1_genome.genes)

        for i in range(genome_length):
            # 50% chance to inherit from each parent
            if random.random() < 0.5:
                child_genes.append(parent1_genome.genes[i].copy())
            else:
                child_genes.append(parent2_genome.genes[i].copy())

        return Genome(
            genes=child_genes,
            metadata={
                'generation': parent1_genome.metadata.get('generation', 0) + 1,
                'parent1_id': parent1_genome.metadata.get('entity_id'),
                'parent2_id': parent2_genome.metadata.get('entity_id')
            }
        )

    @staticmethod
    def mutate(genome: Genome, mutation_rate: float = 0.01) -> Genome:
        """Apply random mutations to genes"""
        for gene in genome.genes:
            if random.random() < mutation_rate:
                # Choose what to mutate
                mutation_type = random.choice(['weight', 'source', 'sink'])

                if mutation_type == 'weight':
                    # Small adjustment to weight
                    gene.weight += random.gauss(0, 0.5)
                    gene.weight = max(-8.0, min(8.0, gene.weight))

                elif mutation_type == 'source':
                    # Change source neuron
                    if gene.source_type == 'input':
                        gene.source_id = random.randint(0, 4)  # 5 input neurons
                    else:
                        gene.source_id = random.randint(0, 1)  # 2 internal neurons

                elif mutation_type == 'sink':
                    # Change sink neuron
                    if gene.sink_type == 'internal':
                        gene.sink_id = random.randint(0, 1)  # 2 internal neurons
                    else:
                        gene.sink_id = random.randint(0, 3)  # 4 output neurons

        return genome

    @staticmethod
    def generate_random_genome(genome_length: int = 16) -> Genome:
        """Create random genome for initial population"""
        genes = []
        for _ in range(genome_length):
            gene = Gene(
                source_type=random.choice(['input', 'internal']),
                source_id=random.randint(0, 4 if random.random() < 0.7 else 1),
                sink_type=random.choice(['internal', 'output']),
                sink_id=random.randint(0, 1 if random.random() < 0.3 else 3),
                weight=random.gauss(0, 2.0)
            )
            genes.append(gene)
        return Genome(genes)

    @staticmethod
    def generate_template_genome(traits: Dict[str, float], genome_length: int = 16) -> Genome:
        """Create genome from user-specified traits"""
        genes = []

        # Encode aggression trait (affects attack output connections)
        aggression = traits.get('aggression', 0.5)  # 0-1
        for i in range(4):  # 4 genes for attack behavior
            genes.append(Gene(
                source_type='input',
                source_id=3,  # threat_distance input
                sink_type='output',
                sink_id=2,  # attack_probability output
                weight=aggression * 6.0 - 3.0  # Map 0-1 to -3 to +3
            ))

        # Encode speed/exploration trait (affects movement)
        exploration = traits.get('exploration', 0.5)
        for i in range(4):
            genes.append(Gene(
                source_type='input',
                source_id=1,  # food_direction_x
                sink_type='output',
                sink_id=0,  # move_x
                weight=exploration * 4.0  # 0 to 4
            ))

        # Encode social trait (affects reproduction)
        social = traits.get('social', 0.5)
        for i in range(4):
            genes.append(Gene(
                source_type='input',
                source_id=4,  # energy input
                sink_type='output',
                sink_id=3,  # reproduce_probability
                weight=social * 4.0 - 2.0
            ))

        # Fill remaining with random genes for evolution potential
        while len(genes) < genome_length:
            genes.append(GeneticOperators.generate_random_genome(1).genes[0])

        return Genome(genes[:genome_length])
```

### Neural Network Implementation

```python
class NeuralNetwork:
    """Simplified feed-forward + recurrent neural network"""

    INPUT_NEURONS = ['hunger_level', 'food_direction_x', 'food_direction_y',
                     'threat_distance', 'energy_ratio']
    OUTPUT_NEURONS = ['move_x', 'move_y', 'attack_probability', 'reproduce_probability']

    def __init__(self, genome: Genome, num_internal: int = 2):
        self.genome = genome
        self.num_internal = num_internal
        self.connections = self._build_connections(genome)
        self.internal_state = [0.0] * num_internal

    def _build_connections(self, genome: Genome) -> Dict[tuple, float]:
        """Convert genome to connection weight dictionary"""
        connections = {}

        for gene in genome.genes:
            # Map gene source to actual neuron name/index
            if gene.source_type == 'input':
                source = self.INPUT_NEURONS[gene.source_id % len(self.INPUT_NEURONS)]
            else:
                source = f'internal_{gene.source_id % self.num_internal}'

            # Map gene sink to actual neuron name/index
            if gene.sink_type == 'internal':
                sink = f'internal_{gene.sink_id % self.num_internal}'
            else:
                sink = self.OUTPUT_NEURONS[gene.sink_id % len(self.OUTPUT_NEURONS)]

            # Add connection (later genes override earlier ones for same connection)
            connections[(source, sink)] = gene.weight

        return connections

    def forward(self, inputs: Dict[str, float]) -> Dict[str, float]:
        """Process inputs through network to produce outputs"""
        # Step 1: Compute internal neuron activations
        new_internal_state = []
        for i in range(self.num_internal):
            neuron_id = f'internal_{i}'
            weighted_sum = 0.0

            # Inputs → Internal
            for input_name, input_value in inputs.items():
                if (input_name, neuron_id) in self.connections:
                    weighted_sum += input_value * self.connections[(input_name, neuron_id)]

            # Internal → Internal (recurrent, using previous state)
            for j in range(self.num_internal):
                other_id = f'internal_{j}'
                if (other_id, neuron_id) in self.connections:
                    weighted_sum += self.internal_state[j] * self.connections[(other_id, neuron_id)]

            # Activation: tanh
            new_internal_state.append(math.tanh(weighted_sum))

        # Update internal state
        self.internal_state = new_internal_state

        # Step 2: Compute output neuron activations
        outputs = {}
        for output_name in self.OUTPUT_NEURONS:
            weighted_sum = 0.0

            # Inputs → Output (direct)
            for input_name, input_value in inputs.items():
                if (input_name, output_name) in self.connections:
                    weighted_sum += input_value * self.connections[(input_name, output_name)]

            # Internal → Output
            for i in range(self.num_internal):
                internal_id = f'internal_{i}'
                if (internal_id, output_name) in self.connections:
                    weighted_sum += self.internal_state[i] * self.connections[(internal_id, output_name)]

            # Activation function
            if 'move' in output_name:
                # Movement: tanh (-1 to 1)
                outputs[output_name] = math.tanh(weighted_sum)
            else:
                # Probabilities: sigmoid (0 to 1)
                outputs[output_name] = 1.0 / (1.0 + math.exp(-weighted_sum))

        return outputs

    def get_sensory_inputs(self, owner: 'Entity', context: 'SimulationContext') -> Dict[str, float]:
        """Gather sensory information from environment"""
        vitality = owner.get_component('VitalityComponent')

        # Input 1: Hunger level (0 = full, 1 = starving)
        hunger_level = vitality.hunger / 100.0 if vitality else 0.5

        # Input 2-3: Direction to nearest food
        food_direction = self._find_nearest_food(owner, context)

        # Input 4: Distance to nearest threat (normalized)
        threat_distance = self._find_nearest_threat(owner, context)

        # Input 5: Current energy ratio
        energy_ratio = vitality.current_energy / vitality.max_energy if vitality else 0.5

        return {
            'hunger_level': hunger_level,
            'food_direction_x': food_direction[0],
            'food_direction_y': food_direction[1],
            'threat_distance': threat_distance,
            'energy_ratio': energy_ratio
        }

    def _find_nearest_food(self, owner: 'Entity', context: 'SimulationContext') -> Tuple[float, float]:
        """Return normalized direction vector to nearest food source"""
        diet = owner.get_component('DietComponent')
        if not diet:
            return (0.0, 0.0)

        # Use existing spatial grid query
        vision_range = owner.stats.entity_vision
        nearby = context.query_nearby_entities(owner.position, vision_range)

        # Filter for edible entities
        food_targets = [e for e in nearby if diet._is_edible(e)]

        if not food_targets:
            return (0.0, 0.0)

        # Find nearest
        nearest = min(food_targets, key=lambda e: owner.position.distance_to(e.position))

        # Direction vector
        direction = (nearest.position - owner.position).normalized()

        return (direction.x, direction.y)

    def _find_nearest_threat(self, owner: 'Entity', context: 'SimulationContext') -> float:
        """Return normalized distance to nearest predator (0 = very close, 1 = far)"""
        vision_range = owner.stats.entity_vision
        nearby = context.query_nearby_entities(owner.position, vision_range)

        # Filter for predators
        threats = [e for e in nearby if self._is_threat(owner, e)]

        if not threats:
            return 1.0  # No threats = max distance

        # Find nearest threat
        nearest = min(threats, key=lambda e: owner.position.distance_to(e.position))
        distance = owner.position.distance_to(nearest.position)

        # Normalize: 0 at 0 distance, 1 at vision_range
        return min(1.0, distance / vision_range)

    def _is_threat(self, owner: 'Entity', other: 'Entity') -> bool:
        """Check if other entity is a predator"""
        from app.simulation.core.types import Trait

        # Herbivore threatened by carnivores and omnivores
        if Trait.HERBIVORE in owner.traits:
            return Trait.CARNIVORE in other.traits or Trait.OMNIVORE in other.traits

        # Carnivores threatened by larger carnivore packs
        if Trait.CARNIVORE in owner.traits:
            if Trait.CARNIVORE in other.traits:
                owner_pack_size = len(owner.pack.members) if owner.pack else 1
                other_pack_size = len(other.pack.members) if other.pack else 1
                return other_pack_size > owner_pack_size * 1.5

        return False
```

### Species Gene Pool Tracking

```python
class SpeciesGenePool:
    """Tracks genetic diversity and evolution for a species"""

    def __init__(self, species_id: str):
        self.species_id = species_id
        self.population_genomes: Dict[str, Genome] = {}  # entity_id → genome
        self.generation_count = 0
        self.births_this_generation = 0
        self.deaths_this_generation = 0
        self.allele_stats = {}

    def record_birth(self, entity_id: str, genome: Genome):
        """Register new entity in gene pool"""
        self.population_genomes[entity_id] = genome
        self.births_this_generation += 1

        # Track generation number
        gen = genome.metadata.get('generation', 0)
        self.generation_count = max(self.generation_count, gen)

    def record_death(self, entity_id: str):
        """Remove entity from gene pool"""
        if entity_id in self.population_genomes:
            del self.population_genomes[entity_id]
            self.deaths_this_generation += 1

    def get_diversity_metrics(self) -> Dict[str, float]:
        """Calculate genetic diversity statistics"""
        if not self.population_genomes:
            return {'diversity': 0.0, 'avg_weight': 0.0, 'weight_variance': 0.0}

        # Collect all weights from all genomes
        all_weights = []
        for genome in self.population_genomes.values():
            all_weights.extend([gene.weight for gene in genome.genes])

        if not all_weights:
            return {'diversity': 0.0, 'avg_weight': 0.0, 'weight_variance': 0.0}

        avg_weight = sum(all_weights) / len(all_weights)
        variance = sum((w - avg_weight) ** 2 for w in all_weights) / len(all_weights)

        return {
            'diversity': variance,  # Higher variance = more genetic diversity
            'avg_weight': avg_weight,
            'weight_variance': variance,
            'population_size': len(self.population_genomes),
            'generation': self.generation_count,
            'birth_rate': self.births_this_generation,
            'death_rate': self.deaths_this_generation
        }

    def get_dominant_traits(self) -> Dict[str, Any]:
        """Identify most common genetic patterns"""
        if not self.population_genomes:
            return {}

        # Count connection patterns
        connection_counts = defaultdict(int)
        for genome in self.population_genomes.values():
            for gene in genome.genes:
                pattern = f"{gene.source_type}_{gene.source_id}->{gene.sink_type}_{gene.sink_id}"
                connection_counts[pattern] += 1

        # Find most common connections
        total_entities = len(self.population_genomes)
        dominant = {pattern: count/total_entities
                   for pattern, count in connection_counts.items()
                   if count/total_entities > 0.5}  # >50% of population has this connection

        return dominant
```

---

## Implementation Phases

### Phase 0: Critical Bug Fixes (Required Foundation)
**Goal:** Make existing simulation functional before adding genetics
**Estimated Time:** 2-3 days
**Priority:** CRITICAL

#### Tasks
1. **Re-enable Energy and Hunger System**
   - File: `server/app/simulation/core/config.py`
   - Change `ENERGY_DECAY_RATE` from 0.0 to 0.4
   - Change `HUNGER_RATE` from 0.0 to 0.15
   - Adjust `REPRODUCTION_THRESHOLD` to 75.0
   - Test balance: creatures should survive ~4 seconds without food

2. **Differentiate Species Stats**
   - File: `server/app/simulation/models/species.py`
   - Add `get_base_stats()` method to Species class
   - Return species-specific EntityStats based on traits:
     - Herbivores: high speed (15), low attack (1), high vision (70)
     - Carnivores: medium speed (8), high attack (10), medium vision (60)
     - Omnivores: balanced stats
     - Plants: 0 speed, low health (30)
   - Update entity creation to use species stats

3. **Implement Basic Reproduction (Non-Genetic)**
   - File: `server/app/simulation/components/base/reproduction.py`
   - Complete ReproductionComponent stub
   - Add mate-finding logic (same species within 20 units)
   - Add energy cost (40 per parent)
   - Create offspring at nearby position
   - Add cooldown timer (10 seconds)
   - Integrate into component factory

4. **Fix Plant Spawning**
   - File: `server/app/simulation/simulation.py`
   - Replace random 10% spawn with density-based spawning
   - Check local plant count (max 5 in 30-unit radius)
   - Reduce global spawn rate to 5%

5. **Balance Energy Economy**
   - Tune food energy values:
     - Plants: 25 (increased from 15)
     - Meat: 45 (increased from 30)
   - Adjust movement cost formula
   - Test: Herbivores should survive average 30-60 seconds
   - Test: Carnivores should catch prey before starving

6. **Add Flee Behavior**
   - File: `server/app/simulation/components/base/diet.py`
   - Detect nearby predators when low health
   - Set flee velocity away from threat
   - Higher priority than food-seeking

#### Success Criteria
✅ Creatures actively seek food to survive
✅ Energy depletes, forcing regular eating
✅ Reproduction creates new entities without errors
✅ Herbivore and carnivore populations both survive 5+ minutes
✅ Plant population remains stable (not explosion or depletion)
✅ Prey flee from predators when threatened

---

### Phase 1: Basic Genome System
**Goal:** Add heritable genetic code without neural networks
**Estimated Time:** 4-5 days
**Priority:** HIGH

#### Tasks
1. **Create Genome Data Structures**
   - New file: `server/app/simulation/genetics/genome.py`
   - Implement `Gene` class (32-bit encoding)
   - Implement `Genome` class (list of genes + metadata)
   - Add hex string serialization
   - Add copy/deepcopy methods

2. **Create Genetic Operators**
   - New file: `server/app/simulation/genetics/operators.py`
   - Implement `crossover(parent1, parent2)` function
   - Implement `mutate(genome, rate)` function
   - Implement `generate_random_genome(length)` function
   - Add unit tests for each operator

3. **Add Genome to Entity**
   - File: `server/app/simulation/models/entity.py`
   - Add `genome: Optional[Genome]` field to Entity
   - Update serialization to include genome (only send on request, not every frame)

4. **Update ReproductionComponent for Genetic Crossover**
   - File: `server/app/simulation/components/base/reproduction.py`
   - Extract parent genomes
   - Apply crossover and mutation
   - Pass child genome to entity creation
   - Track generation number in genome metadata

5. **Create SpeciesGenePool**
   - New file: `server/app/simulation/genetics/gene_pool.py`
   - Implement `SpeciesGenePool` class
   - Add to Species model
   - Track births/deaths
   - Calculate diversity metrics
   - Update on entity lifecycle events

6. **Encode Physical Stats in Genome**
   - Use first N genes to encode max_health, speed, attack, defense
   - Decode genes to numeric stats during entity creation
   - Test: Offspring stats should average parents' stats (±mutation)

#### API Changes
- Add `/api/species/{id}/genome` endpoint for gene pool data
- Add genome field to entity schema (optional, only when requested)
- WebSocket: Add `genome_update` event type for birth notifications

#### Success Criteria
✅ Entities spawn with genomes
✅ Reproduction creates child genomes via crossover
✅ Mutations occur at expected rate
✅ Offspring stats resemble parent stats
✅ Gene pool tracks population diversity
✅ Frontend can fetch and display genome hex strings

---

### Phase 2: Neural Network Brains
**Goal:** Replace hardcoded behaviors with evolved neural networks
**Estimated Time:** 5-7 days
**Priority:** HIGH

#### Tasks
1. **Implement NeuralNetwork Class**
   - New file: `server/app/simulation/genetics/neural_network.py`
   - Build connection dictionary from genome
   - Implement `forward(inputs)` method
   - Support 5 inputs, 2 internal, 4 outputs
   - Add recurrent state tracking
   - Optimize with NumPy for batch processing (if needed)

2. **Implement Sensory Input System**
   - Add `get_sensory_inputs(owner, context)` method
   - Calculate hunger_level from VitalityComponent
   - Find nearest food direction (use existing spatial grid)
   - Find nearest threat distance
   - Get current energy ratio
   - Add age sensor (optional)

3. **Create NeuralBrainComponent**
   - New file: `server/app/simulation/components/neural_brain.py`
   - Initialize with genome
   - Build neural network from genome
   - Update: gather inputs, process network, store outputs
   - Provide accessor methods for outputs

4. **Integrate Brain with PhysicsComponent**
   - File: `server/app/simulation/components/base/physics.py`
   - Check for NeuralBrainComponent
   - If present, use brain's move_x/move_y outputs
   - If absent, fallback to old wander behavior (backward compatibility)

5. **Integrate Brain with DietComponent**
   - File: `server/app/simulation/components/base/diet.py`
   - Check for NeuralBrainComponent
   - If present, use brain's attack_probability output (threshold >0.5)
   - If absent, fallback to automatic food seeking

6. **Integrate Brain with ReproductionComponent**
   - File: `server/app/simulation/components/base/reproduction.py`
   - Check for NeuralBrainComponent
   - If present, require brain's reproduce_probability >0.7 AND energy >threshold
   - If absent, use only energy threshold

7. **Add NeuralBrainComponent to Component Factory**
   - File: `server/app/simulation/factory/component_factory.py`
   - Create NeuralBrainComponent from entity genome
   - Add to all creatures (not plants)

8. **Performance Optimization**
   - Profile neural network computation time
   - If >5ms per frame with 500 entities, optimize:
     - Vectorize with NumPy
     - Cache connection matrices
     - Reduce internal neuron count if needed

#### Success Criteria
✅ Neural networks compute in <1ms per entity
✅ Creatures exhibit diverse movement patterns based on genomes
✅ Attack behavior varies by individual
✅ Some creatures evolve effective food-seeking strategies
✅ Some creatures evolve effective predator-avoidance strategies
✅ No performance regression (still 60 FPS with 500 entities)

---

### Phase 3: Evolution and Natural Selection
**Goal:** Observe evolutionary adaptation over multiple generations
**Estimated Time:** 3-4 days
**Priority:** MEDIUM

#### Tasks
1. **Tune Mutation Rates**
   - Experiment with rates: 0.001, 0.01, 0.05
   - Observe time to adaptation
   - Balance exploration vs. stability
   - Make configurable per species

2. **Add Fitness Tracking**
   - Track entity lifetime
   - Track successful hunts
   - Track food consumed
   - Track offspring produced
   - Store in genome metadata

3. **Create Evolution Visualization**
   - Frontend: Graph population size over time
   - Frontend: Graph average genome diversity
   - Frontend: Show dominant neural connection patterns
   - WebSocket: Send gene pool stats every 5 seconds

4. **Implement Genome Inspector UI**
   - Click entity to view genome
   - Display genome as hex string
   - Visualize neural network (nodes and edges)
   - Show generation number and ancestry
   - Color-code connections by weight (green=positive, red=negative)

5. **Add Evolution Experiments**
   - Test 1: Start with random genomes, observe convergence
   - Test 2: Start with identical genomes, observe divergence via mutation
   - Test 3: Introduce environmental pressure (add obstacle zones)
   - Test 4: Compare evolution speed with different mutation rates

#### Success Criteria
✅ Populations adapt to environmental pressures within 50 generations
✅ Genetic diversity increases from random start, then stabilizes
✅ Successful behaviors (e.g., food-seeking) spread through population
✅ Users can observe evolution in real-time graphs
✅ Genome inspector shows clear differences between successful/unsuccessful entities

---

### Phase 4: User Species Creation
**Goal:** UI for users to design custom species with evolvable traits
**Estimated Time:** 5-6 days
**Priority:** MEDIUM

#### Tasks
1. **Design Species Creation UI**
   - Modal/page for custom species design
   - Trait sliders:
     - Aggression (0-100): Affects attack output bias
     - Exploration (0-100): Affects movement randomness
     - Social (0-100): Affects pack formation and reproduction willingness
     - Speed (0-100): Affects max_velocity gene
     - Resilience (0-100): Affects max_health gene
   - Color picker for species visualization
   - Name input
   - "Deploy Species" button

2. **Implement Genome Template Generator**
   - File: `server/app/simulation/genetics/template_generator.py`
   - Convert trait sliders to genome
   - Create biased genes for each trait:
     - Aggression → input(threat) → output(attack) connections
     - Exploration → input(food) → output(move) connections
     - Social → input(energy) → output(reproduce) connections
   - Add random genes for evolution potential
   - Validate genome structure

3. **Add Species Creation API Endpoint**
   - POST `/api/species/create`
   - Accept traits, color, name, initial_population
   - Generate genome template
   - Create species with gene pool
   - Spawn initial population with slight genetic variation
   - Return species ID

4. **Add Species Management UI**
   - List user-created species
   - Show current population count
   - Show generation count
   - Show evolutionary metrics (avg speed, avg aggression, etc.)
   - Delete species button
   - Add more population button

5. **Implement Trait Inheritance Visualization**
   - Show how trait values change over generations
   - Graph: "Aggression over 100 generations"
   - Overlay population size to correlate traits with success

6. **Add Genome Sharing**
   - Export genome as hex string
   - Import genome from hex string
   - Share successful species with others
   - Preset library of interesting genomes

#### Success Criteria
✅ Users can create custom species via UI in <2 minutes
✅ Trait sliders produce predictable initial behaviors
✅ User species successfully compete with default species
✅ Evolution causes trait drift from initial values
✅ Users can export/import genomes successfully
✅ Interesting evolved behaviors emerge from user-created species

---

### Phase 5: Advanced Features (Optional)
**Goal:** Add depth and complexity to genetic evolution system
**Estimated Time:** Ongoing
**Priority:** LOW

#### Potential Features

1. **Pheromone Communication**
   - 2D grid of pheromone concentrations
   - Entities can emit pheromones (neural output)
   - Entities can sense pheromones (neural input)
   - Decay over time
   - Use cases: trail to food, danger warnings, mating signals

2. **Environmental Zones**
   - Define regions with different properties:
     - Hot/cold zones (energy cost modifiers)
     - Toxic zones (health damage over time)
     - Safe zones (no predators allowed)
     - Rich zones (more plant spawns)
   - Selection pressure drives adaptation to specific zones

3. **Sexual Selection**
   - Mate choice based on fitness indicators
   - Colorful displays (visual traits)
   - Courtship behaviors
   - Female choice leads to runaway evolution (peacock tail effect)

4. **Speciation**
   - Track genetic divergence
   - Prevent mating between distant genomes
   - Automatically create new species when populations diverge
   - Phylogenetic tree visualization

5. **Learning and Memory**
   - Entities remember successful hunting grounds
   - Avoid areas where they were attacked
   - Learn from pack members
   - Combine learning with genetic evolution (Baldwin effect)

6. **Symbiosis and Cooperation**
   - Mutualism: Two species both benefit
   - Parasitism: One species exploits another
   - Commensalism: One benefits, other unaffected
   - Encode cooperation strategies in genome

7. **Larger Neural Networks**
   - Scale to 10 inputs, 5 internal, 8 outputs
   - Add more sensory inputs (smell, hearing)
   - Add more action outputs (vocalize, hide, build shelter)
   - Profile and optimize performance

---

## Performance Analysis

### Computational Cost Estimation

#### Neural Network Per-Entity Cost
```
Operations per forward pass:
- 5 inputs × 2 internal neurons = 10 multiplications
- 2 internal × 2 internal (recurrent) = 4 multiplications
- (5 inputs + 2 internal) × 4 outputs = 28 multiplications
- Total: ~42 floating-point operations + tanh/sigmoid (expensive)

With approximations (fast tanh):
~60-80 CPU cycles per forward pass

500 entities × 80 cycles × 60 FPS = 2.4M cycles/second
On modern CPU (3 GHz): ~0.08% CPU usage
```

**Verdict:** ✅ Negligible performance impact

#### Genome Crossover Cost
```
Reproduction event:
- Crossover: 16 genes × 2 parent lookups = 32 memory accesses
- Mutation: 16 genes × random check = 16 random() calls
- Total: ~200 CPU cycles per reproduction

Assuming 10 births per second:
10 × 200 cycles = 2000 cycles/second
```

**Verdict:** ✅ Trivial cost

#### Memory Footprint
```
Per entity:
- Genome: 16 genes × 20 bytes = 320 bytes
- Neural network: ~40 connections × 16 bytes = 640 bytes
- Total genetic data: ~1 KB per entity

500 entities × 1 KB = 500 KB
```

**Verdict:** ✅ Insignificant memory usage

#### WebSocket Bandwidth
```
Current state broadcast (60 FPS):
- Entity: {id, x, y, health, energy, species_id} = ~50 bytes
- 500 entities × 50 bytes × 60 FPS = 1.5 MB/sec

With genomes (DON'T send every frame):
- Send genome only on birth: ~320 bytes per birth
- 10 births/sec × 320 bytes = 3.2 KB/sec additional

Total bandwidth: 1.5 MB/sec (unchanged)
```

**Verdict:** ✅ No bandwidth impact if genomes sent only on events

### Optimization Strategies

#### If Performance Issues Arise

1. **Vectorize Neural Networks with NumPy**
   ```python
   # Batch process all entities at once
   input_matrix = np.array([entity.get_inputs() for entity in entities])  # Shape: (N, 5)
   internal_matrix = np.tanh(input_matrix @ input_weights)  # Matrix multiplication
   output_matrix = np.tanh(np.hstack([input_matrix, internal_matrix]) @ output_weights)
   ```
   **Expected speedup:** 10-50x for large populations

2. **Reduce Neural Network Size**
   - Use 1 internal neuron instead of 2
   - Remove recurrent connections
   - **Tradeoff:** Less behavioral complexity

3. **Update Frequency Reduction**
   - Update neural networks at 30 FPS instead of 60 FPS
   - Interpolate outputs between updates
   - **Tradeoff:** Slightly less responsive behavior

4. **Spatial Culling**
   - Only update entities near players' viewport
   - Simplify off-screen entities to basic physics
   - **Tradeoff:** Simulation not globally consistent

5. **Multi-threading**
   - Use Python multiprocessing to parallelize entity updates
   - Divide population into chunks, process in parallel
   - **Complexity:** Requires careful synchronization

### Benchmarking Plan

After each implementation phase, measure:
- Average frame time (target: <16ms for 60 FPS)
- Entity update time per entity (target: <0.03ms)
- Memory usage (target: <100 MB for 1000 entities)
- WebSocket latency (target: <50ms)

Run stress tests:
- 500 entities baseline
- 1000 entities stretch goal
- 2000 entities maximum

**Performance budget:**
- Neural network computation: <5ms per frame
- Physics/collision: <5ms per frame
- Reproduction/mutation: <1ms per frame
- Remaining: 5ms buffer

---

## API and Data Structure Changes

### New TypeScript Types (Frontend)

```typescript
// client/src/types/genetics.ts

export interface Gene {
  source_type: 'input' | 'internal';
  source_id: number;
  sink_type: 'internal' | 'output';
  sink_id: number;
  weight: number;
}

export interface Genome {
  genes: Gene[];
  metadata: {
    entity_id?: string;
    generation: number;
    parent1_id?: string;
    parent2_id?: string;
    fitness?: number;
  };
}

export interface GenePoolStats {
  species_id: string;
  population_size: number;
  generation_count: number;
  genetic_diversity: number;
  avg_weight: number;
  birth_rate: number;
  death_rate: number;
  dominant_connections: Record<string, number>;
}

export interface NeuralNetworkVisualization {
  inputs: string[];
  outputs: string[];
  internal_count: number;
  connections: Array<{
    source: string;
    sink: string;
    weight: number;
  }>;
}
```

### Updated Entity Schema

```typescript
// client/src/types/new_simulation.ts

export interface Entity {
  // Existing fields...
  id: string;
  type: EntityType;
  position: Vector2D;
  health: number;
  energy: number;
  species_id: string;

  // New fields
  genome?: Genome;  // Optional, only sent on request
  generation?: number;
  parent_ids?: [string, string];
}
```

### New API Endpoints

```python
# server/app/main.py

@app.get("/api/species/{species_id}/gene_pool")
async def get_gene_pool_stats(species_id: str) -> GenePoolStats:
    """Get genetic diversity statistics for a species"""
    pass

@app.get("/api/entity/{entity_id}/genome")
async def get_entity_genome(entity_id: str) -> Genome:
    """Get full genome for specific entity"""
    pass

@app.get("/api/entity/{entity_id}/neural_network")
async def get_entity_network(entity_id: str) -> NeuralNetworkVisualization:
    """Get neural network structure for visualization"""
    pass

@app.post("/api/species/create")
async def create_custom_species(request: CreateSpeciesRequest) -> Species:
    """Create user-defined species with custom traits"""
    pass

@app.post("/api/species/{species_id}/add_population")
async def add_species_population(species_id: str, count: int) -> None:
    """Spawn additional entities of a species"""
    pass

@app.get("/api/genome/export/{entity_id}")
async def export_genome(entity_id: str) -> str:
    """Export genome as hex string for sharing"""
    pass

@app.post("/api/genome/import")
async def import_genome(hex_string: str) -> Genome:
    """Import genome from hex string"""
    pass
```

### WebSocket Protocol Extensions

```typescript
// New message types

// Server → Client
interface GenomeBirthEvent {
  type: 'genome_birth';
  entity_id: string;
  genome: Genome;
  parent_ids: [string, string];
  generation: number;
}

interface GenePoolUpdate {
  type: 'gene_pool_update';
  species_id: string;
  stats: GenePoolStats;
}

interface EvolutionMilestone {
  type: 'evolution_milestone';
  species_id: string;
  milestone: string;  // e.g., "Generation 100 reached"
  message: string;
}

// Client → Server
interface RequestGenome {
  type: 'request_genome';
  entity_id: string;
}

interface HighlightLineage {
  type: 'highlight_lineage';
  entity_id: string;
  depth: number;  // How many generations back to trace
}
```

### Database Schema Changes (If Using DB)

```sql
-- Optional: Persistent storage for interesting genomes

CREATE TABLE genomes (
  id UUID PRIMARY KEY,
  hex_string TEXT NOT NULL,
  species_id UUID,
  generation INT,
  fitness_score FLOAT,
  created_at TIMESTAMP,
  creator_user_id UUID,
  is_public BOOLEAN,
  description TEXT
);

CREATE TABLE genome_lineage (
  child_genome_id UUID REFERENCES genomes(id),
  parent1_genome_id UUID REFERENCES genomes(id),
  parent2_genome_id UUID REFERENCES genomes(id),
  mutation_count INT
);

CREATE INDEX idx_genomes_species ON genomes(species_id);
CREATE INDEX idx_genomes_fitness ON genomes(fitness_score DESC);
```

---

## Testing Strategy

### Unit Tests

#### Genome Tests
```python
# server/tests/test_genome.py

def test_gene_encoding():
    """Test that genes encode/decode correctly to 32 bits"""
    gene = Gene('input', 3, 'output', 2, 2.5)
    encoded = gene.to_bytes()
    decoded = Gene.from_bytes(encoded)
    assert decoded.source_type == 'input'
    assert decoded.source_id == 3
    assert abs(decoded.weight - 2.5) < 0.01

def test_genome_hex_serialization():
    """Test genome to/from hex string"""
    genome = Genome([
        Gene('input', 0, 'internal', 0, 1.0),
        Gene('internal', 0, 'output', 1, -2.0)
    ])
    hex_str = genome.to_hex_string()
    restored = Genome.from_hex_string(hex_str)
    assert len(restored.genes) == 2
    assert restored.genes[0].source_type == 'input'
```

#### Genetic Operator Tests
```python
# server/tests/test_genetic_operators.py

def test_crossover():
    """Test that crossover mixes parent genes"""
    parent1 = generate_random_genome(16)
    parent2 = generate_random_genome(16)

    child = GeneticOperators.crossover(parent1, parent2)

    assert len(child.genes) == 16
    # Child should have some genes from each parent
    matches_parent1 = sum(1 for c, p in zip(child.genes, parent1.genes) if c == p)
    matches_parent2 = sum(1 for c, p in zip(child.genes, parent2.genes) if c == p)
    assert matches_parent1 > 0 and matches_parent2 > 0

def test_mutation_rate():
    """Test that mutations occur at expected frequency"""
    genome = generate_random_genome(100)
    original_weights = [g.weight for g in genome.genes]

    mutated = GeneticOperators.mutate(genome, mutation_rate=0.1)

    changes = sum(1 for o, m in zip(original_weights, [g.weight for g in mutated.genes]) if o != m)
    # With 100 genes and 10% rate, expect ~10 mutations (allow 5-15 range)
    assert 5 <= changes <= 15
```

#### Neural Network Tests
```python
# server/tests/test_neural_network.py

def test_network_forward_pass():
    """Test that neural network produces valid outputs"""
    genome = generate_random_genome(16)
    network = NeuralNetwork(genome, num_internal=2)

    inputs = {
        'hunger_level': 0.7,
        'food_direction_x': 0.5,
        'food_direction_y': -0.3,
        'threat_distance': 0.9,
        'energy_ratio': 0.6
    }

    outputs = network.forward(inputs)

    # Check output ranges
    assert -1 <= outputs['move_x'] <= 1
    assert -1 <= outputs['move_y'] <= 1
    assert 0 <= outputs['attack_probability'] <= 1
    assert 0 <= outputs['reproduce_probability'] <= 1

def test_network_determinism():
    """Test that same inputs produce same outputs (no randomness)"""
    genome = generate_random_genome(16)
    network = NeuralNetwork(genome, num_internal=2)

    inputs = {...}
    output1 = network.forward(inputs)
    output2 = network.forward(inputs)

    assert output1 == output2
```

### Integration Tests

#### Reproduction Integration
```python
# server/tests/test_reproduction_integration.py

def test_genetic_reproduction_creates_child():
    """Test that reproduction component uses genetic crossover"""
    # Setup: Two entities with different genomes
    parent1 = create_test_entity(genome=generate_random_genome(16))
    parent2 = create_test_entity(genome=generate_random_genome(16))

    # Set high energy for both
    parent1.get_component('VitalityComponent').current_energy = 90
    parent2.get_component('VitalityComponent').current_energy = 90

    # Place near each other
    parent1.position = Vector2D(100, 100)
    parent2.position = Vector2D(105, 105)

    # Trigger reproduction
    repro = parent1.get_component('ReproductionComponent')
    context = setup_test_context([parent1, parent2])
    repro.update(parent1, context, dt=1.0)

    # Check: Child entity should exist
    children = [e for e in context.entities if e.id not in [parent1.id, parent2.id]]
    assert len(children) == 1

    # Check: Child has genome from both parents
    child_genome = children[0].get_component('NeuralBrainComponent').genome
    parent1_genome = parent1.get_component('NeuralBrainComponent').genome
    parent2_genome = parent2.get_component('NeuralBrainComponent').genome

    # Some genes should match each parent
    matches_p1 = sum(1 for c, p in zip(child_genome.genes, parent1_genome.genes) if c == p)
    matches_p2 = sum(1 for c, p in zip(child_genome.genes, parent2_genome.genes) if c == p)
    assert matches_p1 > 0 and matches_p2 > 0
```

#### Evolution Simulation Test
```python
# server/tests/test_evolution.py

def test_selection_pressure_causes_adaptation():
    """Test that evolution improves fitness over generations"""
    # Setup: Simple environment with food at position (500, 500)
    context = setup_test_context()
    spawn_food_at(context, Vector2D(500, 500))

    # Create initial population with random genomes
    species = create_test_species()
    for _ in range(50):
        entity = species.create_entity(random_position())
        context.register(entity)

    # Run simulation for 100 generations (~500 seconds)
    generation_fitness = []
    for gen in range(100):
        # Run one generation (5 seconds)
        for tick in range(300):
            update_all_entities(context, dt=1/60)

        # Measure fitness: average distance to food
        avg_distance = np.mean([
            entity.position.distance_to(Vector2D(500, 500))
            for entity in context.entities
        ])
        generation_fitness.append(avg_distance)

    # Check: Fitness should improve (distance should decrease)
    early_fitness = np.mean(generation_fitness[:10])
    late_fitness = np.mean(generation_fitness[-10:])
    assert late_fitness < early_fitness * 0.8  # 20% improvement
```

### Performance Tests

```python
# server/tests/test_performance.py

def test_neural_network_performance():
    """Benchmark neural network update time"""
    genome = generate_random_genome(16)
    network = NeuralNetwork(genome, num_internal=2)
    inputs = generate_test_inputs()

    iterations = 10000
    start_time = time.perf_counter()

    for _ in range(iterations):
        network.forward(inputs)

    elapsed = time.perf_counter() - start_time
    avg_time = (elapsed / iterations) * 1000  # ms per forward pass

    assert avg_time < 0.01  # Should be under 0.01ms per entity
    print(f"Neural network forward pass: {avg_time:.4f}ms")

def test_500_entity_frame_time():
    """Test full simulation update with 500 entities"""
    context = setup_test_context()

    # Spawn 500 entities with neural networks
    for _ in range(500):
        entity = create_test_entity_with_brain()
        context.register(entity)

    # Measure frame update time
    iterations = 100
    start_time = time.perf_counter()

    for _ in range(iterations):
        update_all_entities(context, dt=1/60)

    elapsed = time.perf_counter() - start_time
    avg_frame_time = (elapsed / iterations) * 1000  # ms

    assert avg_frame_time < 16  # Must maintain 60 FPS
    print(f"500 entity frame time: {avg_frame_time:.2f}ms")
```

### Manual Testing Scenarios

1. **Genetic Inheritance Verification**
   - Create two entities with distinct genomes (one aggressive, one passive)
   - Force reproduction
   - Inspect child genome: should have mix of both parents' genes
   - Verify child behavior is intermediate

2. **Evolution Observation**
   - Start with random genomes
   - Run for 10 minutes
   - Observe population behaviors converge
   - Export successful genome, import to new simulation
   - Verify imported genome performs well immediately

3. **User Species Creation**
   - Use UI to create species with max aggression
   - Deploy into simulation with herbivores
   - Verify high attack rate
   - Create species with max exploration
   - Verify wandering behavior

4. **Performance Stress Test**
   - Spawn 1000 entities
   - Monitor frame rate for 5 minutes
   - Check for memory leaks
   - Verify WebSocket doesn't lag

---

## Future Enhancements

### Potential Research Directions

1. **Multi-Objective Evolution**
   - Evolve for both survival AND reproduction
   - Create trade-offs (strength vs. speed)
   - Observe Pareto-optimal strategies

2. **Co-evolution**
   - Predator and prey evolve together (arms race)
   - Track Red Queen dynamics
   - Measure co-evolutionary cycles

3. **Genetic Programming**
   - Evolve entire behavior trees, not just neural networks
   - Use tree-structured genomes
   - More complex behaviors possible

4. **Swarm Intelligence**
   - Evolve pack coordination strategies
   - Emergent group tactics
   - Compare individual vs. group selection

5. **Artificial Life Metrics**
   - Measure "artificial life quotient"
   - Open-ended evolution (no fitness function)
   - Novelty search instead of objective optimization

6. **Educational Features**
   - Interactive tutorials on evolution
   - Challenges: "Evolve a species that survives in harsh environment"
   - Science classroom integration

### Integration with Existing Plans

This genetic evolution plan complements the existing backend resilience plan:
- **Backend resilience** ensures simulation stability
- **Genetic evolution** ensures simulation interest and longevity

Combined benefits:
- Stable, long-running simulations allow evolution to unfold
- Evolved behaviors create interesting patterns worth preserving
- User-created species benefit from reliable infrastructure

---

## Conclusion

This implementation plan transforms the current multi-species simulation into a **genetic evolution ecosystem** by:

1. **Fixing critical bugs** in the existing system (energy, stats, reproduction)
2. **Adding genome-based inheritance** with sexual reproduction and mutation
3. **Replacing hardcoded behaviors** with evolved neural networks
4. **Enabling user creativity** through custom species creation
5. **Maintaining real-time performance** suitable for web deployment

The result will be a unique simulation that combines:
- ✅ Multi-species ecosystem dynamics (predator-prey cycles)
- ✅ Genetic evolution (natural selection, adaptation)
- ✅ Neural network emergence (unexpected behaviors)
- ✅ User interaction (create and share species)
- ✅ Real-time web visualization (watch evolution happen)

### Next Steps

1. Review and approve this plan
2. Begin Phase 0 (critical bug fixes)
3. Validate basic ecosystem balance
4. Proceed to Phase 1 (genome system)
5. Iterate based on user feedback

**Estimated total time:** 3-5 weeks for Phases 0-3 (core functionality)

---

**Document maintained by:** Development Team
**Last updated:** 2025-10-18
**Version:** 1.0
**Status:** Awaiting approval
