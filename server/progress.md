# Backend Progress (ECS Architecture)

**Framework:** FastAPI 0.110.0 + Python 3.12
**Architecture:** Entity-Component System (ECS)
**Status:** Active development
**Purpose:** Modular, extensible simulation backend

## Quick Commands

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server with hot reload
uvicorn app.main:app --reload

# Run on specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

## Technology Stack

### Core Framework
- **FastAPI:** 0.110.0 - Modern async web framework
- **Uvicorn:** 0.27.1 - ASGI server
- **Python:** 3.12 - Language runtime
- **Pydantic:** 2.6.1 - Data validation and settings

### Real-time Communication
- **WebSockets:** 12.0 - WebSocket protocol implementation
- **asyncio:** Built-in async/await support
- **JSON:** Standard library for serialization

### Data & Computation
- **SQLAlchemy:** 2.0.32 - ORM for database access
- **NumPy:** 1.26.3 - Numerical computations
- **Python dataclasses:** Built-in for data structures

### Testing & Development
- **Pytest:** 8.0.0 - Testing framework
- **pytest-asyncio:** Async test support
- **pytest-cov:** Coverage reporting

## Project Structure

```
server/
├── app/
│   ├── main.py                        # FastAPI app entry point
│   │
│   ├── simulation/
│   │   ├── simulation.py              # Main SimulationManager
│   │   │
│   │   ├── core/
│   │   │   ├── context.py             # SimulationContext (DI container)
│   │   │   ├── interfaces.py          # Component & GameObject protocols
│   │   │   └── vector.py              # Vector2D math operations
│   │   │
│   │   ├── models/
│   │   │   ├── entity.py              # Entity with component system
│   │   │   ├── species.py             # Species definition & factory
│   │   │   ├── pack.py                # Pack/group management
│   │   │   └── enums.py               # EntityType, EntityState, etc.
│   │   │
│   │   ├── components/
│   │   │   ├── base.py                # Base Component class
│   │   │   ├── physics.py             # PhysicsComponent (movement)
│   │   │   ├── vitality.py            # VitalityComponent (health/energy)
│   │   │   ├── reproduction.py        # ReproductionComponent
│   │   │   ├── social.py              # SocialComponent (packs)
│   │   │   │
│   │   │   ├── diet/
│   │   │   │   ├── herbivore.py       # HerbivoreComponent
│   │   │   │   ├── carnivore.py       # CarnivoreComponent
│   │   │   │   └── omnivore.py        # OmnivoreComponent
│   │   │   │
│   │   │   └── behaviors/
│   │   │       ├── hunting.py         # HuntingBehaviorComponent
│   │   │       └── fleeing.py         # (potential)
│   │   │
│   │   └── factory/
│   │       └── component_factory.py   # Component initialization
│   │
│   ├── api/
│   │   └── routes/
│   │       └── simulation.py          # API endpoints & WebSocket
│   │
│   └── config.py                      # Configuration settings
│
├── tests/                             # Test suite
├── requirements.txt                   # Python dependencies
├── .env                              # Environment variables
└── .venv/                            # Virtual environment
```

## Architecture Overview

### Entity-Component System (ECS)

The new backend uses a **component-based architecture** for maximum flexibility and extensibility.

**Key Concepts:**

1. **Entity:** Container for components with unique ID
   - Has position, state, entity type
   - No behavior logic (logic is in components)

2. **Component:** Reusable behavior module
   - Implements specific functionality
   - Can be attached/detached from entities
   - Composable for complex behaviors

3. **System:** Processes entities with specific components
   - SimulationManager acts as the main system
   - Updates components each tick

### Core Classes

**Entity** (`models/entity.py`)
```python
class Entity:
    id: str
    entity_type: EntityType  # CREATURE, PLANT, OBSTACLE
    position: Vector2D
    velocity: Vector2D
    state: EntityState  # SPAWNING, ACTIVE, DORMANT, DYING, DEAD
    species_id: str
    components: Dict[str, Component]

    def add_component(self, component: Component)
    def get_component(self, component_type: str) -> Component
    def update(self, delta_time: float, context: SimulationContext)
```

**Component** (`components/base.py`)
```python
class Component(Protocol):
    """Base protocol for all components"""

    def update(self, game_object: GameObject,
               delta_time: float,
               context: SimulationContext) -> None:
        """Update component logic"""
        pass

    def to_dict(self) -> dict:
        """Serialize component state"""
        pass
```

**SimulationContext** (`core/context.py`)
```python
class SimulationContext:
    """Dependency injection container"""

    world_width: int
    world_height: int
    entities: Dict[str, Entity]
    species: Dict[str, Species]
    packs: Dict[str, Pack]

    def get_nearby_entities(self, position: Vector2D,
                           radius: float) -> List[Entity]
    def spatial_query(self, bounds: Rect) -> List[Entity]
    # ... other utility methods
```

## Component Types

### Core Components

**PhysicsComponent** (`components/physics.py`)
- Handles movement and physics
- Velocity, acceleration, max speed
- World boundary wrapping
- Collision detection (future)

**VitalityComponent** (`components/vitality.py`)
- Health and energy management
- Age and lifetime tracking
- Energy consumption over time
- Death conditions

**ReproductionComponent** (`components/reproduction.py`)
- Reproduction logic
- Self-replicating or two-parent modes
- Energy cost for reproduction
- Spawn new entities

**SocialComponent** (`components/social.py`)
- Pack membership
- Group behaviors
- Communication between entities (future)

### Diet Components

**HerbivoreComponent** (`components/diet/herbivore.py`)
- Seeks and consumes plants
- Energy gain from plant consumption
- Avoids carnivores

**CarnivoreComponent** (`components/diet/carnivore.py`)
- Hunts other creatures
- Energy gain from successful hunts
- Predator behavior

**OmnivoreComponent** (`components/diet/omnivore.py`)
- Can consume both plants and creatures
- Flexible diet strategy
- Opportunistic feeding

### Behavior Components

**HuntingBehaviorComponent** (`components/behaviors/hunting.py`)
- Advanced hunting logic
- Target selection
- Chase behavior
- Attack mechanics

## Species System

**Species** (`models/species.py`)
```python
class Species:
    id: str
    name: str
    entity_type: EntityType
    traits: SpeciesTraits
    color: str
    component_config: Dict[str, Any]
```

**SpeciesTraits:**
- **Diet:** Herbivore, Carnivore, Omnivore
- **Reproduction:** SelfReplicating, TwoParents
- **Mobility:** (future) Fast, Slow, Stationary
- **Social:** (future) Solitary, Pack, Swarm

**Component Factory** (`factory/component_factory.py`)
- Creates components based on species traits
- Initializes component parameters
- Ensures correct component composition

Example:
```python
# Herbivore creature gets:
- PhysicsComponent (for movement)
- VitalityComponent (for health/energy)
- HerbivoreComponent (for diet)
- ReproductionComponent (for spawning)
- SocialComponent (if pack-based)
```

## Simulation Loop

**Fixed Timestep:** 16ms (60 FPS target)

```python
async def run_simulation():
    accumulator = 0.0
    fixed_timestep = 0.016  # 16ms

    while running:
        frame_start = time.time()

        # Accumulate time
        accumulator += delta_time

        # Update with fixed timestep
        while accumulator >= fixed_timestep:
            update_entities(fixed_timestep)
            accumulator -= fixed_timestep

        # Broadcast state
        await broadcast_state()

        # Sleep to maintain 60 FPS
        await asyncio.sleep(max(0, fixed_timestep - elapsed))
```

**Update Pipeline:**
1. Update each entity's components
2. Process component interactions (eating, hunting, etc.)
3. Handle entity lifecycle (spawning, death)
4. Update pack memberships
5. Clean up dead entities
6. Increment tick counter

## WebSocket Protocol

### Endpoint
```
ws://localhost:8000/ws/simulation
```

### Message Format

**Client → Server:**

Start simulation:
```json
{"type": "start"}
```

Pause simulation:
```json
{"type": "pause"}
```

Add species:
```json
{
  "type": "add_species",
  "data": {
    "name": "Herbivores",
    "entity_type": "CREATURE",
    "count": 10,
    "traits": {
      "diet": "HERBIVORE",
      "reproduction": "SELF_REPLICATING"
    },
    "color": "#00ff00"
  }
}
```

Heartbeat:
```json
{"type": "ping"}
```

**Server → Client:**

State broadcast (60 FPS):
```json
{
  "entities": [
    {
      "id": "entity_123",
      "entity_type": "CREATURE",
      "position": [100.5, 200.3],
      "velocity": [1.2, -0.5],
      "species_id": "species_abc",
      "state": "ACTIVE",
      "components": {
        "vitality": {"health": 85, "energy": 60},
        "social": {"pack_id": "pack_xyz"}
      }
    }
  ],
  "species": [
    {
      "id": "species_abc",
      "name": "Herbivores",
      "color": "#00ff00",
      "traits": {"diet": "HERBIVORE"}
    }
  ],
  "packs": [
    {
      "id": "pack_xyz",
      "member_ids": ["entity_123", "entity_456"]
    }
  ],
  "tick": 3600,
  "delta_time": 16.67,
  "state": "running"
}
```

## API Endpoints

### HTTP Endpoints

**GET /** - Welcome message
```
Returns: {"message": "Game of Life Simulation API"}
```

**GET /health** - Health check
```
Returns: {
  "status": "healthy",
  "simulation": "running|paused|stopped",
  "entities": 150,
  "species": 3
}
```

### WebSocket Endpoint

**WS /ws/simulation** - Real-time simulation connection
- Bidirectional communication
- JSON message protocol
- 60 FPS state broadcasts
- Connection management with heartbeat

## Configuration

### Environment Variables (.env)

```bash
# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1

# CORS
CORS_ORIGINS=http://localhost:5173,https://simulation.aaryareddy.com

# Database
DATABASE_URL=sqlite:///./simulation.db

# Simulation
WORLD_WIDTH=800
WORLD_HEIGHT=600
TICK_RATE=60
```

### FastAPI Config (`config.py`)

```python
class Settings(BaseSettings):
    app_name: str = "Game of Life Simulation"
    world_width: int = 800
    world_height: int = 600
    tick_rate: int = 60
    cors_origins: list = ["*"]

    class Config:
        env_file = ".env"
```

## Completed Features

**ECS Architecture:**
- Protocol-based component system
- GameObject interface for type safety
- SimulationContext for dependency injection
- Vector2D math operations

**Entity System:**
- Full entity lifecycle (spawn, active, dying, dead)
- Component attachment/detachment
- State machine management
- Efficient entity updates

**Component Library:**
- PhysicsComponent - movement and forces
- VitalityComponent - health/energy/age
- ReproductionComponent - spawning logic
- SocialComponent - pack membership
- Diet components (herbivore, carnivore, omnivore)
- HuntingBehaviorComponent - advanced hunting

**Species Management:**
- Trait-based species definition
- Component factory for initialization
- Multiple species support
- Species-specific configurations

**Pack System:**
- Pack creation and management
- Member tracking
- Pack-based behaviors (foundation)

**Simulation Engine:**
- Fixed timestep simulation loop
- Asyncio-based concurrency
- 60 FPS target with accumulator
- Efficient state broadcasting

**WebSocket Communication:**
- Full-duplex communication
- JSON protocol
- Connection health monitoring
- Error handling and reconnection

**API Layer:**
- RESTful health endpoints
- WebSocket endpoint
- CORS configuration
- Request validation with Pydantic

## Work in Progress

**Modified Files (Git Status):**
- `app/simulation/core/context.py` - Context refactoring
- `app/simulation/core/interfaces.py` - Protocol updates
- `app/simulation/models/entity.py` - Component integration
- `app/simulation/models/pack.py` - Pack behavior improvements
- `app/simulation/models/species.py` - Species factory enhancements
- `app/simulation/simulation.py` - Main loop optimization

**Current Development:**
- Refining component protocols for better type safety
- Optimizing entity updates for performance
- Improving pack AI and social behaviors
- Testing with frontend's new components
- Fine-tuning reproduction mechanics

## Testing

**Test Structure:**
```bash
tests/
├── conftest.py                 # Pytest fixtures
├── test_entities.py           # Entity tests
├── test_components.py         # Component tests
├── test_simulation.py         # Simulation loop tests
└── test_api.py               # API endpoint tests
```

**Running Tests:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_entities.py

# With coverage
pytest --cov=app --cov-report=html

# Async tests
pytest -v tests/test_simulation.py
```

## Performance Considerations

**Optimizations:**
- Spatial partitioning for entity queries (planned)
- Component update batching
- Efficient serialization for WebSocket
- Entity pooling to reduce allocations
- Async I/O for non-blocking operations

**Scalability:**
- Current target: 1000+ entities at 60 FPS
- Bottleneck: Entity updates and collision detection
- Solution: Spatial hashing, quad-tree, or grid-based partitioning

**Memory Management:**
- Reuse entity objects when possible
- Lazy loading for large simulations
- Periodic garbage collection triggers

## Database Integration (Future)

**Planned Features:**
- Persistent world state
- Save/load simulations
- Historical data tracking
- User accounts and preferences

**Schema (Planned):**
```sql
-- Simulations table
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP,
    world_width INT,
    world_height INT
);

-- Snapshots table (for save/load)
CREATE TABLE snapshots (
    id UUID PRIMARY KEY,
    simulation_id UUID,
    tick INT,
    state_json TEXT,
    created_at TIMESTAMP
);
```

## Architecture Evolution

**Comparison with Legacy Implementation:**

| Feature | Legacy Server | Current Server (ECS) |
|---------|---------------------|---------------------------|
| Architecture | Monolithic | Entity-Component System |
| Entity Model | Particle class | Entity + Components |
| Extensibility | Limited | Highly modular |
| Type Safety | Partial | Protocol-based |
| Testing | Minimal | Comprehensive |
| Dependencies | Fewer | More modern stack |

**Migration Completed:**
The codebase has fully migrated from the monolithic architecture to the ECS system. The legacy implementation is documented in `docs/server-legacy.md` for historical reference.

## Development Workflow

### Adding a New Component

1. Create component file in `app/simulation/components/`
2. Implement `Component` protocol:
   ```python
   class MyComponent:
       def update(self, game_object, delta_time, context):
           # Component logic
           pass

       def to_dict(self):
           return {"type": "my_component", "data": ...}
   ```

3. Register in component factory
4. Add to species trait configuration
5. Write tests

### Adding a New Entity Type

1. Add to `EntityType` enum in `models/enums.py`
2. Define component composition in species factory
3. Add rendering logic to frontend
4. Update type definitions

### Adding a New API Endpoint

1. Add route in `app/api/routes/`
2. Define Pydantic models for request/response
3. Implement handler
4. Add to FastAPI router
5. Document in this file

## Troubleshooting

**WebSocket Disconnects:**
- Check heartbeat implementation
- Verify client timeout settings
- Ensure async tasks don't block event loop

**Performance Degradation:**
- Profile with `cProfile` or `py-spy`
- Check entity count and update frequency
- Monitor memory usage
- Review component update complexity

**Type Errors:**
- Ensure protocols are implemented correctly
- Use `mypy` for static type checking:
  ```bash
  pip install mypy
  mypy app/
  ```

**Import Errors:**
- Verify virtual environment is activated
- Check Python version (requires 3.12)
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

**Immediate:**
1. Complete protocol refinements
2. Test with new frontend components
3. Optimize entity update performance
4. Add comprehensive logging

**Short-term:**
5. Implement spatial partitioning
6. Add advanced AI behaviors
7. Expand test coverage to 80%+
8. Add admin API for simulation management

**Long-term:**
9. Database persistence layer
10. Genetics and evolution system
11. Multi-simulation support
12. Distributed simulation (multi-process/multi-server)

## Related Documentation

- See `/progress.md` for overall project status
- See `/client/progress.md` for frontend integration details
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- WebSockets: https://websockets.readthedocs.io/
