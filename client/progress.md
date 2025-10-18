# Frontend Progress - Game of Life Simulation Client

**Framework:** React 18.3.1 + TypeScript 5.6.2
**Build Tool:** Vite 5.4.9
**Rendering Engine:** PixiJS 8.5.2
**Status:** Active development - integrating with new backend

## Quick Commands

```bash
# Install dependencies
npm install

# Run development server (default: http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Lint code
npm run lint
```

## Technology Stack

### Core Dependencies
- **React:** 18.3.1 - UI framework
- **TypeScript:** 5.6.2 - Type safety
- **Vite:** 5.4.9 - Build tool and dev server
- **Bun:** Package manager (using bun.lockb)

### Rendering & Graphics
- **PixiJS:** 8.5.2 - GPU-accelerated 2D rendering engine
- **@pixi/react:** 7.1.2 - React bindings for PixiJS
- **Canvas API:** For 2D rendering in new components

### UI & Styling
- **Radix UI:** Component primitives (dialog, select, slider, etc.)
- **Tailwind CSS:** 3.4.14 - Utility-first CSS framework
- **Lucide React:** Icon library
- **class-variance-authority:** Component variants
- **clsx/tailwind-merge:** Conditional styling

### Data & Communication
- **Axios:** HTTP client for API requests
- **WebSocket API:** Native WebSocket for real-time updates
- **Socket.io-client:** 4.8.0 (available but may not be in use)

### Routing
- **React Router DOM:** 6.27.0 - Client-side routing

## Project Structure

```
client/
├── src/
│   ├── components/
│   │   ├── SimulationController.tsx    # Original simulation UI
│   │   ├── SimulationRenderer.tsx      # Original PixiJS renderer
│   │   ├── NewSimulationController.tsx # New UI for refactored backend (WIP)
│   │   ├── NewSimulationRenderer.tsx   # New Canvas renderer (WIP)
│   │   └── ui/                         # Reusable UI components
│   │
│   ├── types/
│   │   ├── simulation.ts               # Original type definitions (modified)
│   │   └── new_simulation.ts           # New type definitions for ECS backend (WIP)
│   │
│   ├── lib/
│   │   └── utils.ts                    # Utility functions
│   │
│   ├── App.tsx                         # Main app with routing (modified)
│   ├── App.css                         # Global styles
│   └── main.tsx                        # App entry point
│
├── public/
│   └── health.txt                      # Health check endpoint
│
├── index.html                          # HTML template
├── package.json                        # Dependencies and scripts
├── vite.config.ts                      # Vite configuration
├── tailwind.config.js                  # Tailwind configuration
├── tsconfig.json                       # TypeScript configuration
├── tsconfig.node.json                  # TS config for Node files
└── bun.lockb                           # Bun lock file
```

## Component Overview

### Current Implementation

**NewSimulationController.tsx** (untracked)
- Controller for refactored ECS backend
- Integrates with `/server` API
- Updated WebSocket message handling
- Compatible with new entity/component schema
- Uses `new_simulation.ts` types

**NewSimulationRenderer.tsx** (untracked)
- Canvas-based rendering (alternative to PixiJS)
- Renders entities from ECS backend
- Supports new state structure
- Optimized for component-based entities

### Routing

**App.tsx**
```typescript
// Routes configured:
/ - Landing page
/newsim - Simulation (NewSimulationController)
```

The simulation is accessed via the `/newsim` route.

## Type Definitions

### Original Types (`simulation.ts`)

```typescript
// Core entity representation
interface Particle {
  id: string
  position: [number, number]
  velocity: [number, number]
  species_id: string
  energy: number
  health: number
  age: number
  // ... additional properties
}

interface Species {
  id: string
  name: string
  color: string
  traits: SpeciesTraits
  // ...
}

interface ParticleGroup {
  id: string
  particles: string[]  // particle IDs
  // ...
}
```

### New Types (`new_simulation.ts`) - Work in Progress

Expected to align with ECS architecture:
```typescript
// Component-based entity
interface Entity {
  id: string
  entity_type: 'CREATURE' | 'PLANT' | 'OBSTACLE'
  components: Component[]
  state: EntityState
  // ...
}

interface Component {
  type: string
  // Component-specific data
}

// Species with traits
interface Species {
  id: string
  name: string
  entity_type: EntityType
  traits: SpeciesTraits
  // ...
}
```

## WebSocket Protocol

### Connection
```typescript
const ws = new WebSocket(VITE_WS_URL + '/ws/simulation')
```

### Message Types

**From Client:**
```json
{"type": "start"}
{"type": "pause"}
{"type": "ping"}
{"type": "add_species", "data": {...}}
```

**From Server:**
```json
{
  "entities": [...],
  "species": [...],
  "packs": [...],
  "tick": 12345,
  "delta_time": 16.67,
  "state": "running"
}
```

### State Updates
- Frequency: 60 FPS (every ~16ms)
- Format: Full state snapshot (entities, species, packs)
- All entities sent each frame for rendering

## Rendering System

### PixiJS Renderer (Original)

**Features:**
- GPU-accelerated rendering via WebGL
- Sprite-based particle rendering
- Container hierarchy for organization
- Graphics primitives (circles, lines, rectangles)
- Text labels for debugging

**Render Pipeline:**
1. Clear previous frame containers
2. Draw grid (if enabled)
3. Draw vision ranges (if enabled)
4. Draw particles as sprites
5. Draw health/energy bars
6. Draw pack connections
7. Draw debug info

**Performance:**
- Hardware acceleration via WebGL
- Batch rendering for sprites
- Efficient for large particle counts

### Canvas Renderer (New)

**Features:**
- Canvas 2D API
- Direct pixel manipulation
- Simpler integration with React
- May be more suitable for ECS entity rendering

**Render Pipeline:**
1. Clear canvas
2. Transform context for camera
3. Draw entities with component-based rendering
4. Draw UI overlays

## Configuration

### Environment Variables (.env)

```bash
# WebSocket URL for backend connection
VITE_WS_URL=ws://localhost:8000

# For production:
# VITE_WS_URL=wss://simulation.aaryareddy.com
```

### Vite Config

**Key Settings:**
- Port: 5173 (default)
- Proxy: Can be configured for API requests
- Build output: `dist/`
- Asset optimization
- Hot Module Replacement (HMR)

## Completed Features

**UI Controls:**
- Start/pause/stop simulation
- Species creation form
- Species trait configuration (diet, reproduction)
- Settings toggles (grid, vision, energy, packs)
- Real-time statistics display

**Visualization:**
- Particle/entity rendering
- Color-coded species
- Grid overlay
- Vision range circles
- Energy/health indicators
- Direction indicators
- Pack connection visualization
- Child entity highlighting

**State Management:**
- WebSocket connection handling
- Reconnection logic
- Message queue for commands
- Local state for UI controls
- Simulation state synchronization

**Responsive Design:**
- Canvas sizing
- Control panel layout
- Mobile-friendly controls (partial)

## Work in Progress

**New Backend Integration:**
- NewSimulationController component development
- NewSimulationRenderer with Canvas API
- Type definitions for ECS entities
- WebSocket protocol updates for component system
- Testing at `/newsim` route

**Modified Files (Git Status):**
- `App.tsx` - Added new route for testing
- `types/simulation.ts` - Updated for compatibility

**Untracked Files:**
- `components/NewSimulationController.tsx` - New controller
- `components/NewSimulationRenderer.tsx` - New renderer
- `types/new_simulation.ts` - New type definitions

## Development Workflow

### Local Development

1. **Start Backend:**
   ```bash
   cd ../server
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   npm run dev
   ```

3. **Access:**
   - Landing page: http://localhost:5173/
   - Simulation: http://localhost:5173/newsim

### Build for Production

```bash
# Build optimized bundle
npm run build

# Output in dist/ directory
# Static files ready for deployment
```

### Docker Development

```bash
# From project root
docker-compose up frontend

# Frontend runs on configured port
# Hot reload may not work in container
```

## Performance Considerations

**PixiJS Advantages:**
- GPU acceleration for thousands of particles
- Efficient batch rendering
- Built-in sprite pooling
- Good for particle-heavy simulations

**Canvas API Considerations:**
- CPU-based rendering
- Simpler API, easier to debug
- May be sufficient for moderate entity counts
- Better integration with React lifecycle

**Optimization Strategies:**
- Throttle render updates if FPS drops
- Implement culling for off-screen entities
- Use object pooling for frequently created/destroyed elements
- Debounce UI controls
- Lazy load components

## Troubleshooting

**WebSocket Connection Failed:**
- Check `VITE_WS_URL` in .env
- Ensure backend is running
- Verify CORS configuration on backend
- Check browser console for errors

**Build Errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check TypeScript errors: `npm run type-check`

**Hot Reload Not Working:**
- Restart dev server
- Check for syntax errors in components
- Verify file watchers aren't at limit (Linux)

**Performance Issues:**
- Enable FPS counter in dev tools
- Reduce particle count
- Disable vision/pack overlays
- Check for memory leaks in components

## Next Steps

1. Complete NewSimulationController integration
2. Test new Canvas renderer performance vs PixiJS
3. Update all type definitions for ECS entities
4. Add comprehensive error handling
5. Implement loading states and fallbacks
6. Add user preferences persistence (localStorage)
7. Improve mobile responsiveness
8. Add keyboard shortcuts
9. Implement simulation recording/playback
10. Add performance metrics overlay

## Related Documentation

- See `/progress.md` for overall project status
- See `/server/progress.md` for backend API details
- See Vite docs: https://vitejs.dev/
- See PixiJS docs: https://pixijs.com/
- See React docs: https://react.dev/
