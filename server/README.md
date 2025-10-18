# Game of Life Backend (ECS Architecture)

Modern Entity-Component System (ECS) implementation of the multi-species particle simulation backend.

## Architecture

This backend uses an **Entity-Component System** design pattern for maximum flexibility and extensibility:

- **Entities** - Containers with unique IDs
- **Components** - Modular behaviors (Physics, Vitality, Diet, Reproduction)
- **SimulationContext** - Dependency injection container
- **SimulationManager** - Processes entities at 60 FPS

### Key Components

| Component | Purpose |
|-----------|---------|
| `PhysicsComponent` | Position, velocity, collision detection |
| `VitalityComponent` | Energy, health, lifespan |
| `DietComponent` | Herbivore, carnivore, omnivore behaviors |
| `ReproductionComponent` | Self-replicating or two-parent reproduction |

### Directory Structure

```
app/
├── main.py                      # FastAPI entry point, WebSocket endpoint
├── simulation/
│   ├── simulation.py            # SimulationManager (main loop)
│   ├── components/              # Component implementations
│   │   ├── physics.py
│   │   ├── vitality.py
│   │   ├── diet.py
│   │   └── reproduction.py
│   ├── models/                  # Data models
│   │   ├── entity.py            # Entity container
│   │   ├── species.py           # Species configuration
│   │   └── pack.py              # Pack/group management
│   └── core/                    # Core types and interfaces
│       ├── types.py             # Enums (EntityType, Trait)
│       ├── interfaces.py        # Protocols (Component, GameObject)
│       └── context.py           # SimulationContext (DI container)
```

## Quick Start

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Using Docker

```bash
# Development mode (with hot reloading)
docker compose -f ../docker-compose.dev.yml up backend

# Production mode
docker compose -f ../docker-compose.yml up backend
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ws/simulation` | WebSocket | Real-time simulation updates (60 FPS) |
| `/api/health` | GET | Health check |
| `/api/status` | GET | Detailed simulation status |
| `/docs` | GET | Swagger UI documentation |

## WebSocket Protocol

### Client Messages

```json
{"type": "start"}                                    // Start simulation
{"type": "pause"}                                    // Pause simulation
{"type": "pong"}                                     // Heartbeat response
{"type": "add_species", "name": "...", ...}         // Add new species
```

### Server Messages

```json
{
  "entities": [...],      // Array of entity states
  "species": {...},       // Species configurations
  "packs": {...},        // Pack information
  "tick": 1234,          // Simulation tick number
  "delta_time": 16.67,   // Time since last update (ms)
  "state": "running"     // "running" | "paused"
}
```

## Adding New Components

1. Create component class in `app/simulation/components/`
2. Implement the `Component` protocol from `core/interfaces.py`
3. Register in `SimulationContext` factory
4. Add trait mapping in species configuration

Example:
```python
# app/simulation/components/new_component.py
from app.simulation.core.interfaces import Component

class NewComponent(Component):
    def __init__(self, config: dict):
        self.value = config.get("value", 0)

    def update(self, delta_time: float, context: SimulationContext):
        # Update logic here
        pass

    def to_dict(self) -> dict:
        return {"value": self.value}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `DEBUG` | `false` | Enable debug mode |
| `WORLD_WIDTH` | `800` | Simulation world width |
| `WORLD_HEIGHT` | `600` | Simulation world height |
| `SIMULATION_FPS` | `60` | Target frames per second |

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_simulation.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run only unit tests (exclude slow integration tests)
uv run pytest -m "not slow"
```

## Development

See [DEVELOPMENT.md](../DEVELOPMENT.md) for comprehensive local development guide.

Quick commands:
```bash
# Start native development
../scripts/dev-native.sh

# Start Docker development
../scripts/dev.sh --backend-only

# Format code
uv run black app/
uv run isort app/

# Type check
uv run mypy app/

# Lint
uv run flake8 app/
```

## Architecture Evolution

This ECS implementation replaces a previous monolithic architecture. Key improvements:

- ✅ Modular component system (easy to extend)
- ✅ Better separation of concerns
- ✅ Trait-based composition vs inheritance
- ✅ Improved testability
- ✅ Type-safe with protocols
- ✅ Dependency injection

## Performance

- Targets 60 FPS for smooth simulation
- Efficient WebSocket broadcasting
- Spatial partitioning for collision detection (TODO)
- Quadtree optimization for large entity counts (TODO)

## Contributing

1. Write tests for new features
2. Follow type hints and protocols
3. Use `black` and `isort` for formatting
4. Update this README if adding major features

## License

See [LICENSE](../LICENSE) in root directory.
