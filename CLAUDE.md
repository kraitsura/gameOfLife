# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-species particle simulation inspired by Conway's Game of Life, built with an Entity-Component System (ECS) architecture for modularity and extensibility.

Key aspects:
- **Frontend**: React with Canvas API for GPU-accelerated rendering at `/newsim`
- **Backend**: ECS architecture in `/server` with component-based entity behaviors
- **Real-time**: WebSocket communication at 60 FPS

## Common Development Commands

### Frontend Development
```bash
cd client
npm install                  # Install dependencies
npm run dev                  # Start dev server on localhost:3000
npm run build               # Production build
npm run lint                # Run ESLint
npm run typecheck           # TypeScript compilation check
npm test                    # Run Vitest tests
```

### Backend Development

**Prerequisites**: Install [uv](https://docs.astral.sh/uv/) (fast Python package manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

**Development workflow**:
```bash
cd server
uv sync                     # Create venv + install all dependencies (including dev)
uv run uvicorn app.main:app --reload --port 8000   # Start server
uv run pytest               # Run all tests
uv run pytest tests/test_simulation.py -v          # Specific test file

# Add new dependencies
uv add fastapi              # Add production dependency
uv add --dev pytest         # Add dev dependency

# Update dependencies
uv lock                     # Update lockfile
uv sync                     # Sync environment with lockfile
```

**Note**: `uv` automatically manages virtual environments and is 10-100x faster than pip. The `uv.lock` file ensures reproducible builds.

### Local Development (Recommended)

**Quick Start** - Choose your workflow:

```bash
# Option 1: Docker-based (consistent environment, no local setup)
./scripts/dev.sh

# Option 2: Native (fastest hot reload, requires uv + npm/bun)
./scripts/dev-native.sh

# Option 3: Hybrid (backend in Docker, frontend native)
./scripts/dev.sh --backend-only
cd client && npm run dev
```

**Development features:**
- ✅ Hot reloading for both backend (uvicorn --reload) and frontend (Vite HMR)
- ✅ Automatic health checks and dependency syncing
- ✅ Volume mounts for instant code changes (Docker mode)
- ✅ Combined log output (Native mode)

**Service URLs:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/simulation
- API Docs: http://localhost:8000/docs

**Environment:**
- `.env.development` - Shared dev config (committed)
- `.env.local` - Personal overrides (gitignored, copy from `.env.local.example`)

**See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed setup, debugging, and troubleshooting.**

### Docker Deployment (Production)
```bash
docker-compose up -d        # Start all services
docker-compose logs -f      # View logs
docker-compose down         # Stop services
```

## High-Level Architecture

### Frontend Structure
The frontend is a React application with Canvas API rendering:
- **Route**: `/newsim` → `NewSimulationController.tsx` + `NewSimulationRenderer.tsx`
- **Rendering**: Canvas API for efficient particle visualization
- **Communication**: WebSocket connection to backend for real-time updates

### Backend Architecture (ECS)

The backend (`/server`) implements an Entity-Component System where:
- **Entities** are containers for components (`server/app/simulation/models/entity.py`)
- **Components** define behaviors (physics, vitality, diet, reproduction in `server/app/simulation/components/`)
- **SimulationContext** acts as dependency injection container (`server/app/simulation/core/context.py`)
- **SimulationManager** processes entities at 60 FPS (`server/app/simulation/simulation.py`)

Component initialization is trait-driven through the factory pattern, allowing dynamic behavior composition.

### WebSocket Protocol

Client sends:
```json
{"type": "start|pause|ping|add_species", "data": {...}}
```

Server broadcasts (60 FPS):
```json
{
  "entities": [...],
  "species": [...],
  "packs": [...],
  "tick": number,
  "delta_time": 16.67,
  "state": "running|paused"
}
```

### Architecture Notes

The codebase uses a clean ECS architecture:
- Frontend types are defined in `new_simulation.ts` for ECS compatibility
- Backend components are modularized with protocol-based interfaces
- Pack and species models support dynamic behavior composition
- All features use the component-based system for extensibility

**Legacy Implementation**: A previous monolithic backend implementation has been archived. See `docs/server-legacy.md` for historical context and unique algorithms from that implementation.

## Key Files and Their Purpose

| File | Purpose |
|------|---------|
| `client/src/App.tsx` | Main routing - contains `/newsim` route |
| `client/src/types/new_simulation.ts` | TypeScript types for ECS backend |
| `server/app/main.py` | FastAPI entry point with WebSocket endpoint |
| `server/app/simulation/core/interfaces.py` | Component and GameObject protocols |
| `server/app/simulation/simulation.py` | Main simulation loop (60 FPS) |
| `server/pyproject.toml` | Python project config and dependencies |
| `server/Dockerfile.dev` | Development Docker image with hot reloading |
| `server/Dockerfile` | Production Docker image |
| `**/uv.lock` | Lockfile for reproducible Python dependency resolution |
| `docs/server-legacy.md` | Documentation of previous monolithic backend (archived) |
| `docker-compose.yml` | Production container orchestration |
| `docker-compose.dev.yml` | Development container orchestration with volume mounts |
| `.env.development` | Shared development environment variables |
| `.env.local` | Personal dev overrides (gitignored) |
| `scripts/dev.sh` | Docker-based development startup script |
| `scripts/dev-native.sh` | Native development startup script |
| `DEVELOPMENT.md` | Comprehensive local development guide |
| `nginx/nginx.conf` | WebSocket upgrade configuration |

## Testing Strategy

- **Frontend**: Component tests with Vitest and React Testing Library
- **Backend**: Async tests with pytest, including WebSocket communication tests
- **Integration**: End-to-end testing of WebSocket communication and rendering
- Always run type checking (`npm run typecheck`) before committing frontend changes
- Test WebSocket reconnection logic when modifying connection handlers
- Test component interactions in the ECS system