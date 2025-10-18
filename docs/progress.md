# Game of Life Multi-Species Simulation - Project Progress

**Status:** Active Development - Backend Migration in Progress
**Deployment:** Hetzner VPS at simulation.aaryareddy.com
**Last Major Update:** Backend refactor to Entity-Component System (commit 5910428)

## Quick Start

### Development Setup

**Frontend:**
```bash
cd client
npm install
npm run dev
```

**Backend:**
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Production Deployment

```bash
# Build and start all services with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Configuration

- Copy `.env.example` to `.env.development` or `.env.production`
- Configure `DOMAIN`, `CORS_ORIGINS`, and `VITE_WS_URL`
- For production, ensure SSL certificates are set up via Let's Encrypt/Certbot

## Project Overview

This is a multi-species simulation inspired by Conway's Game of Life, featuring:
- Real-time particle systems with creatures and plants
- Multiple species with different traits (herbivore, carnivore, omnivore)
- Pack/group social dynamics
- Component-based entity system for extensibility
- 60 FPS WebSocket streaming to clients
- GPU-accelerated 2D rendering with PixiJS

## Technology Stack

### Frontend
- **Framework:** React 18.3.1 with TypeScript 5.6.2
- **Build Tool:** Vite 5.4.9
- **Package Manager:** Bun (bun.lockb)
- **Rendering:** PixiJS 8.5.2 via React bindings for GPU-accelerated 2D graphics
- **UI Components:** Radix UI
- **Styling:** Tailwind CSS 3.4.14
- **HTTP Client:** Axios
- **Routing:** React Router DOM

### Backend
- **Framework:** FastAPI 0.110.0 (async Python web framework)
- **Server:** Uvicorn 0.27.1 (ASGI server)
- **Language:** Python 3.12
- **Real-time:** WebSockets 12.0 for 60 FPS state streaming
- **Validation:** Pydantic 2.6.1
- **Database:** SQLAlchemy 2.0.32 ORM
- **Computation:** NumPy 1.26.3
- **Testing:** Pytest 8.0.0

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy:** Nginx with WebSocket upgrade support
- **SSL/TLS:** Let's Encrypt via Certbot
- **Hosting:** Hetzner VPS
- **Domain:** simulation.aaryareddy.com

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                   │
│              (SSL, WebSocket Upgrade, CORS)              │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │
       ┌───────────▼──────────┐  ┌───▼──────────────────┐
       │   React Frontend     │  │  FastAPI Backend     │
       │   (Vite + PixiJS)    │  │  (test-server)       │
       │                      │  │                      │
       │  - Simulation UI     │  │  - Entity-Component  │
       │  - Canvas Renderer   │  │    System            │
       │  - Controls          │  │  - Physics Engine    │
       └──────────────────────┘  │  - WebSocket Server  │
                                 └──────────────────────┘
```

### Client-Server Communication
- **Protocol:** WebSocket at `/ws/simulation`
- **Format:** JSON state updates
- **Frequency:** 60 FPS (16ms timestep)
- **Message Types:**
  - State broadcasts (entities, species, packs, tick count)
  - Control messages: `start`, `pause`, `add_species`
  - Heartbeat: `ping`/`pong`

## Current Status

### Completed Features

**Simulation Engine:**
- Fixed timestep simulation loop (60 FPS)
- Entity lifecycle management (SPAWNING, ACTIVE, DORMANT, DYING, DEAD)
- Physics system with position, velocity, acceleration
- World wrapping at boundaries (800x600 world)
- Energy and health tracking
- Age and lifetime management

**Entity Types:**
- CREATURE - Mobile, can consume resources
- PLANT - Static/slow, renewable resource

**Traits System:**
- Diet types: Herbivore, Carnivore, Omnivore
- Reproduction modes: Self-replicating, Two-parents

**Species Management:**
- Create and configure multiple species
- Track species statistics
- Component factory for trait-based initialization

**Pack/Group System:**
- Social grouping mechanics
- Pack membership tracking
- Visual representation of pack connections

**Rendering:**
- Canvas-based 2D rendering
- Grid overlay toggle
- Vision range visualization
- Energy/health indicators
- Direction indicators
- Pack connection lines (dashed)
- Child entity highlighting

**Infrastructure:**
- Docker containerization for all services
- Nginx reverse proxy with WebSocket support
- Health checks on frontend and backend
- SSL/TLS certificate management
- CORS configuration
- Gzip compression

### Work in Progress

**Active Development:**
- Refining entity models with component system
- Enhanced SimulationContext for dependency injection
- Protocol-based interfaces for loose coupling
- Frontend optimization and feature additions

**Modified Files (Git Status):**
- `client/src/App.tsx` - Routing updates
- `client/src/types/new_simulation.ts` - Type definitions
- `server/app/simulation/core/context.py` - Context refactor
- `server/app/simulation/core/interfaces.py` - Component protocols
- `server/app/simulation/models/entity.py` - ECS entity model
- `server/app/simulation/models/pack.py` - Pack management
- `server/app/simulation/models/species.py` - Species factory
- `server/app/simulation/simulation.py` - Main simulation manager

## Project Structure

```
gameOfLife/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/    # UI components and renderers
│   │   ├── types/         # TypeScript definitions
│   │   └── App.tsx        # Main app with routing
│   ├── package.json
│   └── vite.config.ts
│
├── server/                # ECS-based backend
│   ├── app/
│   │   ├── simulation/
│   │   │   ├── core/      # Base interfaces, context
│   │   │   ├── models/    # Entity, Species, Pack
│   │   │   ├── components/ # Behavior components
│   │   │   ├── factory/   # Component initialization
│   │   │   └── simulation.py
│   │   └── main.py        # FastAPI app
│   └── pyproject.toml
│
├── docs/                  # Documentation
│   └── server-legacy.md   # Legacy implementation reference
│
├── nginx/                 # Nginx configuration
├── certbot/              # SSL certificate management
├── docker-compose.yml    # Container orchestration
├── .env.development      # Dev environment config
└── .env.production       # Prod environment config
```

## Recent Accomplishments

**Major Backend Refactor (Commit 5910428):**
- Implemented Entity-Component System architecture
- 40+ new files with modular design
- Component-based architecture for extensibility
- Type-safe protocols for components and game objects
- Improved separation of concerns

**Codebase Cleanup:**
- Removed legacy monolithic backend
- Removed deprecated /sim route and components
- Consolidated to single ECS backend architecture
- Comprehensive legacy documentation preserved

**Infrastructure Stabilization:**
- 25+ iterations of nginx configuration fixes (v1-v25)
- WebSocket upgrade handling
- Security headers (CSP, X-Frame-Options, XSS-Protection)
- Request logging and compression

## Development Roadmap

**Immediate Next Steps:**
1. Optimize ECS component performance
2. Enhance frontend rendering and interactions
3. Add comprehensive testing coverage
4. Improve documentation

**Future Enhancements:**
- Obstacle entity type
- Advanced AI behaviors (hunting, fleeing, foraging)
- Genetics and evolution system
- Persistent world state (database integration)
- Performance optimizations (spatial partitioning)
- Multiplayer support
- Save/load simulation states

## Deployment Details

**Hosting:** Hetzner VPS
**Domain:** simulation.aaryareddy.com
**SSL:** Let's Encrypt (auto-renewal via Certbot)
**Container Services:**
- Frontend (React/Vite build)
- Backend (FastAPI with Uvicorn)
- Nginx (Reverse proxy)

**Health Endpoints:**
- Frontend: `/health.txt`
- Backend: `/health` (includes simulation state check)

## Troubleshooting

**WebSocket Connection Issues:**
- Check nginx WebSocket upgrade configuration
- Verify CORS origins in backend .env
- Ensure `VITE_WS_URL` matches deployment URL

**Docker Issues:**
- Rebuild containers: `docker-compose build --no-cache`
- Check logs: `docker-compose logs -f [service_name]`
- Verify .env file is loaded: `docker-compose config`

**Development Port Conflicts:**
- Frontend default: 5173
- Backend default: 8000
- Change in respective config files if needed

## Additional Documentation

- See `/client/progress.md` for frontend-specific details
- See `/server/progress.md` for backend architecture deep-dive
- See `/docs/server-legacy.md` for legacy implementation notes
