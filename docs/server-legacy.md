# Legacy Backend Server (/server) - Complete Documentation

**Status**: DEPRECATED - Deleted on 2025-10-17
**Replaced By**: `/server` (ECS architecture)
**Purpose**: Historical reference for unique algorithms and implementation details

---

## Table of Contents

1. [File Structure](#file-structure)
2. [Architecture Overview](#architecture-overview)
3. [Unique Business Logic](#unique-business-logic)
4. [API Endpoints](#api-endpoints)
5. [WebSocket Protocol](#websocket-protocol)
6. [Configuration](#configuration)
7. [Dependencies](#dependencies)
8. [Migration Notes](#migration-notes)

---

## File Structure

```
server/
├── app/
│   ├── core/
│   │   └── config.py              # Pydantic Settings configuration
│   ├── models/
│   │   └── simulation.py          # Core data models (Particle, Species, ParticleGroup)
│   ├── simulation/
│   │   ├── simulation_manager.py  # Main simulation coordinator
│   │   ├── particle_manager.py    # Particle lifecycle and behaviors
│   │   └── group_manager.py       # Group/pack formation logic
│   └── main.py                    # FastAPI app and WebSocket endpoint
├── .env                           # Environment variables (world size, FPS)
├── .gitignore                     # Python artifacts
├── Dockerfile                     # Production container image
├── pyproject.toml                 # uv-based project config
├── uv.lock                        # Dependency lockfile
├── requirements.txt               # Legacy pip requirements
├── requirements.dev.txt           # Development dependencies
├── README.md                      # Status and usage docs
└── progress.md                    # Deprecation notice
```

---

## Architecture Overview

### Monolithic Manager-Based Pattern

Unlike the current ECS (Entity-Component System) architecture in `/server`, the legacy server used a **manager-based pattern**:

- **SimulationManager**: Orchestrates the simulation loop at 60 FPS
- **ParticleManager**: Handles all particle logic (movement, eating, reproduction)
- **GroupManager**: Manages pack formation and dissolution

This architecture had all logic tightly coupled in manager classes, making it harder to extend with new behaviors compared to the component-based ECS approach.

---

## Unique Business Logic

### 1. Plant Spawning System

**Location**: `simulation_manager.py` lines 79-86

```python
plant_spawn_rate: float = 0.1  # 10% chance per tick
if random.random() < self.plant_spawn_rate:
    # Spawns plants randomly during simulation
```

**Key Feature**: Plants spawn dynamically during simulation with 10% probability per tick, creating a sustainable ecosystem.

**Migration Status**: NOT implemented in current server. Plants are only created at initialization.

---

### 2. Energy-Based Plant Decay with Visual Feedback

**Location**: `particle_manager.py` lines 141-157

```python
# Plants gradually decay and change color based on energy
energy_percentage = plant.attributes.energy / 100
g = int(255 * energy_percentage)  # Green fades as energy decreases
plant.color = f"#{r:02x}{g:02x}{b:02x}"
```

**Key Feature**: Plants visually fade from green to brown as they lose energy, providing visual feedback on ecosystem health.

**Migration Status**: NOT implemented in current server.

---

### 3. High Energy/Hunger Tracking for Reproduction

**Location**: `particle_manager.py` lines 175-178

```python
# Tracks sustained high energy + hunger state
if particle.attributes.energy > 90 and particle.attributes.hunger > 90:
    particle.attributes.highEnergyHungerTime += 1
# Self-replicating requires 50+ ticks of this state
```

**Key Feature**: Prevents instant reproduction by requiring 50 consecutive ticks of high energy AND high hunger. Creates more realistic population dynamics.

**Migration Status**: NOT implemented in current server. Reproduction is simpler.

---

### 4. Meeting Counter for Two-Parent Reproduction

**Location**: `particle_manager.py` lines 285-292

```python
# Particles must "meet" twice before reproducing
meeting_count = particle.attributes.meetingCount.get(mate.id, 0)
if meeting_count >= 2:
    return True
# Increments both particles' counters each encounter
```

**Key Feature**: Two-parent reproduction requires particles to meet twice, simulating courtship behavior.

**Migration Status**: NOT implemented in current server.

---

### 5. Diet-Based Vision Filtering

**Location**: `particle_manager.py` lines 188-196

```python
# Carnivores COMPLETELY IGNORE plants (can't see them)
if particle.attributes.diet == Diet.CARNIVORE and
   other.rules.particleType == ParticleType.PLANT:
    continue

# Herbivores/omnivores only see plants when hungry (hunger >= 50)
```

**Key Feature**: Carnivores cannot see plants at all. Herbivores/omnivores only notice plants when hungry (>= 50 hunger).

**Migration Status**: Partially implemented in current server diet component.

---

### 6. Species-Specific Flocking Behavior

**Location**: `particle_manager.py` lines 212-227

```python
# Separation from ALL particles (collision avoidance)
# Cohesion/alignment ONLY with same species
# 2x stronger separation force for different species
```

**Key Feature**: Boids-style flocking with species preference:
- **Separation**: Applied to all nearby particles (collision avoidance)
- **Cohesion**: Only applied to same species (group bonding)
- **Alignment**: Only applied to same species (coordinated movement)
- **Cross-species**: 2x stronger separation from different species

**Migration Status**: Implemented in current server physics component.

---

### 7. Energy Transfer During Eating

**Location**: `particle_manager.py` lines 446-454

```python
# Plants: Fixed 30 energy gain
# Creatures: 70% of prey's energy transferred
# Reduces hunger by energy_gain amount
```

**Energy Transfer Rules**:
- Eating plants: Always gain 30 energy
- Eating creatures: Gain 70% of prey's current energy
- Hunger reduction: Equals energy gained

**Migration Status**: Implemented in current server diet component.

---

### 8. Group Lifecycle Management

**Location**: `group_manager.py` lines 134-149

**Group Formation**:
- Created automatically when two parents reproduce
- Initial members: parent1 + parent2 + child

**Group Benefits**:
- Members gain 0.1 energy per tick while in group

**Leave Conditions**:
- Children leave when age > 100 ticks (maturity)
- Parents leave when energy >= 70 AND random(packMentality)
- Any member can randomly leave based on (1 - packMentality)

**Group Dissolution**:
- Automatically dissolve when < 2 members remain

**Migration Status**: Implemented in current server pack model with different mechanics.

---

### 9. Hardcoded Species Configurations

**Location**: `main.py` lines 52-118

The server initialized with 4 species on startup:

| Species | Color | Type | Diet | Reproduction | Count | Special Traits |
|---------|-------|------|------|--------------|-------|----------------|
| Plants | #2ECC71 | PLANT | Herbivore | Self-replicating | 50 | maxSpeed=0, reproductionRate=0.02 |
| Herbivores | #3498DB | Creature | Herbivore | Two-parent | 20 | visionRange=60, maxSpeed=1.5 |
| Carnivores | #E74C3C | Creature | Carnivore | Self-replicating | 8 | visionRange=80, maxSpeed=2.0 |
| Omnivores | #9B59B6 | Creature | Omnivore | Two-parent | 12 | visionRange=70, maxSpeed=1.8 |

**Migration Status**: Current server uses factory pattern for species creation.

---

## API Endpoints

### WebSocket Endpoints

#### `/ws/simulation` (Primary endpoint)

**Client → Server Messages:**
```json
{"type": "start"}                              // Start simulation
{"type": "pause"}                              // Pause simulation
{"type": "pong"}                               // Heartbeat response
{"type": "add_species", "data": {...}}         // Add new species
```

**Server → Client Broadcasts (60 FPS):**
```json
{
  "particles": {
    "uuid": {
      "id": "uuid",
      "position": {"x": 0.0, "y": 0.0},
      "velocity": {"x": 0.0, "y": 0.0},
      "attributes": {
        "energy": 100.0,
        "hunger": 0.0,
        "size": 3.0,
        "age": 0,
        "lastReproduced": 0,
        "lastAte": 0,
        "diet": "herbivore|carnivore|omnivore",
        "reproductionStyle": "self_replicating|two_parents",
        "packMentality": 0.5,
        "highEnergyHungerTime": 0,
        "meetingCount": {},
        "groupId": "uuid|null",
        "isChild": false,
        "timeInGroup": 0
      },
      "rules": {
        "reproductionRate": 0.001,
        "energyConsumption": 0.05,
        "maxSpeed": 1.5,
        "visionRange": 60.0,
        "socialDistance": 20.0,
        "particleType": "creature|plant"
      },
      "speciesId": "uuid",
      "color": "#RRGGBB"
    }
  },
  "species": {
    "uuid": {
      "id": "uuid",
      "name": "Species Name",
      "color": "#RRGGBB",
      "baseRules": {...},
      "population": 0,
      "diet": "herbivore|carnivore|omnivore",
      "reproductionStyle": "self_replicating|two_parents"
    }
  },
  "groups": {
    "uuid": {
      "id": "uuid",
      "memberIds": ["uuid1", "uuid2"],
      "speciesId": "uuid",
      "parentIds": ["uuid1", "uuid2"],
      "childId": "uuid|null"
    }
  },
  "worldWidth": 800,
  "worldHeight": 600,
  "tickCount": 0
}
```

**Heartbeat**: Server sends `{"type": "ping"}` every 30 seconds.

#### `/ws/health` (Health check endpoint)
- Accepts connection, sends "healthy", immediately closes
- Returns True/False for monitoring

### HTTP Endpoints

#### `GET /health`
```json
{"status": "healthy"}
// 503 on error: {"status": "unhealthy", "message": "..."}
```

#### `GET /status` (Detailed monitoring)
```json
{
  "status": "healthy",
  "simulation": {
    "active": true,
    "species_count": 4,
    "total_particles": 90
  },
  "websocket_connections": 2
}
```

---

## WebSocket Protocol

### Connection Management

```python
# Global connection tracking
active_connections: Set[WebSocket]

# Broadcasting at 60 FPS
async def broadcast_state():
    while True:
        state = simulation.get_state()
        if active_connections:  # Only broadcast if clients connected
            await asyncio.gather(
                *[connection.send_json(state) for connection in active_connections]
            )
        await asyncio.sleep(1/60)  # 60 FPS
```

### State Broadcasting Features

1. **Lazy Broadcasting**: Only sends data when clients are connected
2. **Timeout Protection**: Uses `asyncio.wait_for()` with 1s timeout to prevent blocking
3. **Set-to-List Conversion**: Groups' `memberIds` and `parentIds` converted to lists for JSON serialization

```python
for group in state_dict['groups'].values():
    group['memberIds'] = list(group['memberIds'])
    if group['parentIds'] is not None:
        group['parentIds'] = list(group['parentIds'])
```

---

## Configuration

### Environment Variables

```bash
PROJECT_NAME="Game Of Life"
SIMULATION_FPS=60
WORLD_WIDTH=1000
WORLD_HEIGHT=1000
```

### CORS Configuration

**Location**: `main.py`

```python
# Defaults if CORS_ORIGINS env var not set
CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS',
  '["http://localhost",
    "https://simulation.aaryareddy.com",
    "http://simulation.aaryareddy.com"]'))
```

### Simulation Constants

**Location**: `simulation_manager.py`
```python
tick_rate = 1/60              # 60 FPS
plant_spawn_rate = 0.1        # 10% chance per tick
```

**Location**: `particle_manager.py`
```python
# Energy/hunger thresholds
REPRODUCE_ENERGY_MIN = 90
REPRODUCE_HUNGER_MIN = 90
HIGH_ENERGY_HUNGER_TIME_MIN = 50  # ticks
DEATH_ENERGY = 0
DEATH_HUNGER = 150

# Reproduction requirements
MEETING_COUNT_REQUIRED = 2        # for two-parent
ENERGY_RESTING_BONUS = 0.02       # when speed < 0.1
HUNGER_INCREASE_RATE = 0.05       # per tick

# Group behavior
GROUP_LEAVE_ENERGY = 70
CHILD_MATURITY_AGE = 100
GROUP_ENERGY_BONUS = 0.1          # per tick in group

# Eating mechanics
PLANT_ENERGY_GAIN = 30            # fixed
CREATURE_ENERGY_TRANSFER = 0.7    # 70% of prey's energy
```

---

## Dependencies

### Production Dependencies

```toml
fastapi==0.110.0
uvicorn==0.27.1
websockets==12.0
pydantic==2.6.1
python-dotenv==1.0.0
httpx==0.26.0
numpy==1.26.3              # NOT used in current code
sqlalchemy==2.0.32         # NOT used in current code
pydantic-settings>=2.0.0
```

**Note**: `numpy` and `sqlalchemy` listed but **not imported anywhere** - likely legacy dependencies.

### Development Dependencies

```toml
pytest==7.4.4
pytest-asyncio==0.23.5
pytest-cov==4.1.0
debugpy==1.8.0
ipython==8.12.0
black==23.12.1
flake8==7.0.0
mypy==1.8.0
isort==5.13.2
mkdocs==1.5.3
mkdocs-material==9.5.3
```

**Test Status**: NO test files existed in the codebase.

---

## Migration Notes

### What Was UNIQUE to Legacy /server (NOT in Current Server)

1. **Plant spawning rate system** (0.1 probability per tick)
2. **Energy-based color fading for plants** (visual decay)
3. **High energy/hunger time tracking** (50 tick requirement)
4. **Meeting counter for mate selection** (must meet 2x)
5. **Diet-based vision filtering** (carnivores can't see plants)
6. **Species-specific flocking** (cohesion/alignment only with same species)
7. **Hardcoded startup species** (4 species auto-initialized)
8. **Group energy bonus** (0.1 per tick)
9. **Child maturity age tracking** (leaves group at 100 ticks)
10. **Pack mentality mutation** (±0.1 during reproduction)

### Comparison: Legacy /server vs Current /server

| Feature | Legacy /server | Current /server (ECS) |
|---------|------------------|-------------------|
| Architecture | Monolithic managers | Component-based ECS |
| File count | 6 Python files | 30+ Python files |
| Extensibility | Hardcoded behaviors | Pluggable components |
| Type safety | Basic Pydantic | Protocols + Pydantic |
| Testing | 0 test files | Comprehensive tests |
| Documentation | Minimal | Extensive |
| Spatial optimization | None (O(n²) checks) | SpatialGrid (O(n) with grid) |

### Performance Implications

**Legacy Server Limitations**:
- O(n²) complexity for neighbor detection (no spatial partitioning)
- All logic in monolithic classes
- Difficult to add new behaviors without modifying core classes

**ECS Benefits**:
- O(n) complexity with SpatialGrid
- Pluggable component system
- Easy to add new behaviors via component composition

---

## Docker Deployment

### Production Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Install dependencies (frozen, no dev deps)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy app and run with 4 workers
COPY . .
CMD ["uv", "run", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Used in**: `docker-compose.yml` (production deployment)
**Port**: 8000
**Workers**: 4 (for production stability)

---

## Summary

The legacy server was a proof-of-concept implementation that validated the multi-species particle simulation concept. While functional, it had architectural limitations that made it difficult to extend with new behaviors.

Key takeaways from this implementation have been incorporated into the new ECS architecture, including:
- Flocking behaviors
- Energy transfer mechanics
- Pack/group dynamics
- Diet-based interactions

The unique algorithms documented here (plant spawning, meeting counters, visual decay) remain available for potential future integration if desired.

**Deleted**: 2025-10-17
**Git History**: Available for reference at commit `5910428` and earlier
