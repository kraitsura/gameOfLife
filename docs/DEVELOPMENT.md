# Development Guide

This guide covers local development setup for the Game of Life simulation project.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Approaches](#development-approaches)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Development Workflows](#development-workflows)
- [Testing](#testing)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

## Quick Start

Choose your preferred development approach:

### Option 1: Docker (Recommended for beginners)
```bash
./scripts/dev.sh
```
Open http://localhost:5173

### Option 2: Native (Fastest for active development)
```bash
./scripts/dev-native.sh
```
Open http://localhost:5173

### Option 3: Hybrid (Backend in Docker, Frontend native)
```bash
# Terminal 1: Start backend
./scripts/dev.sh --backend-only

# Terminal 2: Start frontend
cd client && npm run dev
```

## Development Approaches

### 🐳 Docker-Based Development

**Pros:**
- Consistent environment across machines
- No local tool installation needed (except Docker)
- Closer to production setup
- Easy to share with team

**Cons:**
- Slightly slower file watching
- Higher resource usage
- Requires Docker Desktop/Engine

**Setup:**
```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop

# Start all services
./scripts/dev.sh

# Start backend only
./scripts/dev.sh --backend-only --logs

# Rebuild containers
./scripts/dev.sh --build

# Stop services
./scripts/dev.sh --down
```

### ⚡ Native Development

**Pros:**
- Fastest hot reloading
- Lower resource usage
- Direct process access for debugging
- No Docker overhead

**Cons:**
- Requires all tools installed locally
- Environment inconsistencies possible
- Manual dependency management

**Setup:**
```bash
# Install prerequisites
curl -LsSf https://astral.sh/uv/install.sh | sh  # uv
curl -fsSL https://bun.sh/install | bash         # bun (or use npm)

# Start all services
./scripts/dev-native.sh

# Press Ctrl+C to stop
```

### 🔀 Hybrid Development

**Best of both worlds:** Backend in Docker (consistency), Frontend native (speed)

```bash
# Terminal 1
./scripts/dev.sh --backend-only

# Terminal 2
cd client && npm run dev
```

## Prerequisites

### Docker Approach
- [Docker Desktop](https://www.docker.com/products/docker-desktop) or Docker Engine
- [Docker Compose](https://docs.docker.com/compose/install/) v2.0+

### Native Approach
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- [Bun](https://bun.sh) or [Node.js](https://nodejs.org) 18+
- Git

### Install uv (Python Package Manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### Install Bun (JavaScript Runtime - Optional)
```bash
# macOS/Linux
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"
```

## Environment Configuration

### Configuration Files

| File | Purpose | Tracked in Git? |
|------|---------|----------------|
| `.env.development` | Shared development config | ✅ Yes |
| `.env.local` | Personal overrides | ❌ No (gitignored) |
| `.env.local.example` | Template for .env.local | ✅ Yes |

### Setup Environment Variables

1. **Copy the local template:**
   ```bash
   cp .env.local.example .env.local
   ```

2. **Customize .env.local** (optional):
   ```bash
   # Example customizations
   DEBUG=true
   LOG_LEVEL=DEBUG
   WORLD_WIDTH=1200
   WORLD_HEIGHT=800
   ```

3. **Environment precedence:**
   - `.env.local` overrides `.env.development`
   - Docker: Both files are loaded automatically
   - Native: Scripts load both files

## Development Workflows

### Backend Development (server)

#### Using Docker
```bash
# Start with logs
./scripts/dev.sh --backend-only --logs

# Make changes to server/app/**/*.py
# Changes auto-reload thanks to --reload flag

# Run tests
docker compose -f docker-compose.dev.yml exec backend uv run pytest

# Access shell
docker compose -f docker-compose.dev.yml exec backend bash
```

#### Using Native/uv
```bash
cd server

# Install/sync dependencies
uv sync

# Run with auto-reload
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_simulation.py -v

# Add new dependency
uv add fastapi-users

# Add dev dependency
uv add --dev pytest-mock
```

### Frontend Development (client)

#### Using Docker
```bash
# Start frontend
docker compose -f docker-compose.dev.yml up frontend

# Make changes to client/src/**/*.tsx
# Hot Module Replacement (HMR) auto-reloads

# Run tests
docker compose -f docker-compose.dev.yml exec frontend bun test
```

#### Using Native
```bash
cd client

# Install dependencies
npm install  # or: bun install

# Start dev server
npm run dev  # or: bun run dev

# Run tests
npm test     # or: bun test

# Type check
npm run typecheck

# Lint
npm run lint
```

### Full Stack Development

#### Scenario: Adding a new species trait

1. **Backend (server/app/simulation/)**
   ```bash
   # Edit trait enum
   vim server/app/simulation/core/types.py

   # Add component logic
   vim server/app/simulation/components/diet.py

   # Backend auto-reloads
   ```

2. **Frontend (client/src/)**
   ```bash
   # Update types
   vim client/src/types/new_simulation.ts

   # Update UI
   vim client/src/components/NewSimulationController.tsx

   # Frontend auto-reloads
   ```

3. **Test end-to-end**
   - Open http://localhost:5173/newsim
   - Add species with new trait
   - Verify WebSocket updates

## Testing

### Backend Tests

```bash
# Docker
docker compose -f docker-compose.dev.yml exec backend uv run pytest

# Native
cd server
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=html

# Specific test file
uv run pytest tests/test_simulation.py -v

# Run with markers
uv run pytest -m "not slow"
```

### Frontend Tests

```bash
# Docker
docker compose -f docker-compose.dev.yml exec frontend bun test

# Native
cd client
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# UI mode
npm test -- --ui
```

### Integration Testing

Test the backend:

```bash
# Terminal 1: Start server
cd server && uv run uvicorn app.main:app --port 8000 --reload

# Terminal 2: Start frontend
cd client && npm run dev

# Access:
# http://localhost:5173/newsim
```

## Debugging

### Backend Debugging

#### Using VS Code
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/server",
      "env": {
        "DEBUG": "true"
      }
    }
  ]
}
```

#### Using debugpy (Remote)
```python
# Add to server/app/main.py
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger attach...")
debugpy.wait_for_client()
```

#### Logs
```bash
# Docker
docker compose -f docker-compose.dev.yml logs -f backend

# Native
tail -f scripts/logs/backend.log

# Set log level
export LOG_LEVEL=DEBUG
```

### Frontend Debugging

#### Browser DevTools
- React DevTools: Install extension
- Network tab: Monitor WebSocket messages
- Console: View application logs

#### VS Code Debugging
```json
// .vscode/launch.json
{
  "name": "Launch Chrome",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:5173",
  "webRoot": "${workspaceFolder}/client"
}
```

## Troubleshooting

### Common Issues

#### Port Already in Use

**Error:** `Address already in use: 0.0.0.0:8000`

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uv run uvicorn app.main:app --port 8001
```

#### Dependencies Out of Sync

**Error:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Backend (Docker)
./scripts/dev.sh --build

# Backend (Native)
cd server && uv sync

# Frontend
cd client && npm install
```

#### Hot Reload Not Working

**Docker:**
```bash
# Check volume mounts
docker compose -f docker-compose.dev.yml config | grep volumes

# Rebuild
./scripts/dev.sh --build
```

**Native:**
```bash
# macOS: Increase file watch limit
# Linux: Increase inotify watchers
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### WebSocket Connection Fails

**Check:**
1. Backend is running and healthy: http://localhost:8000/api/health
2. CORS is configured: Check server/app/main.py
3. Frontend WebSocket URL: Check VITE_WS_URL in .env.development
4. Browser console for errors

**Debug:**
```bash
# Test WebSocket manually
npm install -g wscat
wscat -c ws://localhost:8000/ws/simulation
```

#### WebSocket "400 Bad Request" (Large Headers/Cookies)

**Error:** WebSocket connection fails with `400 Bad Request` in Chrome, but works in Safari or incognito mode.

**Cause:** Chrome is sending HTTP headers > 8KB during WebSocket handshake, typically from:
- Large cookies from other localhost projects (e.g., Supabase, Auth0)
- Browser extensions injecting headers (ad blockers, privacy tools)
- Accumulated session/debug data in cookies

**Diagnosis:**

1. **Check if it's browser-specific:**
   ```bash
   # Test in Chrome incognito mode (disables extensions)
   # Test in Safari
   # If it works → cookies/extensions are the issue
   ```

2. **Check backend logs:**
   ```bash
   tail -f scripts/logs/backend.log
   # Look for "Large WebSocket headers detected" warnings
   ```

3. **Inspect cookies:**
   - Open Chrome DevTools (F12)
   - Application tab → Storage → Cookies
   - Check `localhost:5173` and `localhost:8000`
   - Look for large cookies (> 1KB) or many cookies

**Solutions:**

**Option 1: Clear localhost cookies (Quick fix)**
```bash
# Chrome DevTools → Application tab → Storage → Cookies
# Right-click on "localhost:5173" → Clear
# Right-click on "localhost:8000" → Clear
# Refresh page
```

**Option 2: Disable problematic extension**
```bash
# If incognito works, identify extension:
# 1. Enable extensions one-by-one in incognito
# 2. Test WebSocket connection after each
# 3. Disable problematic extension
```

**Option 3: Increase header limits (Already configured)**
The project is already configured to handle large headers via environment variables:
- `WEBSOCKETS_MAX_LINE_LENGTH=32768` (32KB)
- `WEBSOCKETS_MAX_NUM_HEADERS=256`

If these are not set, add to `.env.development`:
```bash
WEBSOCKETS_MAX_LINE_LENGTH=32768
WEBSOCKETS_MAX_NUM_HEADERS=256
```

**Prevention:**
- Periodically clear localhost cookies during development
- Use specific cookie paths to prevent cross-project cookie sharing
- Test in incognito mode to catch extension-related issues
- Monitor backend logs for header size warnings

**Note:** This issue typically only occurs in development. Production won't have localhost cookies from other projects.

#### Docker Build Fails

**Error:** `failed to solve with frontend dockerfile.v0`

**Solution:**
```bash
# Clean Docker cache
docker builder prune

# Rebuild from scratch
./scripts/dev.sh --build

# Check Dockerfile syntax
docker compose -f docker-compose.dev.yml config
```

#### uv Lock File Issues

**Error:** `lock file is out of date`

**Solution:**
```bash
cd server
uv lock --upgrade
uv sync
```

### Performance Issues

#### Slow Hot Reload (Docker)

- Use `:cached` volume mounts (already configured)
- Exclude node_modules (already configured)
- Use uv cache volume (already configured)

#### High Memory Usage

```bash
# Check Docker stats
docker stats

# Limit container memory
# Add to docker-compose.dev.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

### Getting Help

1. **Check logs:**
   ```bash
   # Docker
   docker compose -f docker-compose.dev.yml logs

   # Native
   tail -f scripts/logs/*.log
   ```

2. **Check service health:**
   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/status
   ```

3. **Verify environment:**
   ```bash
   # Docker
   docker compose -f docker-compose.dev.yml exec backend env

   # Native
   cd server && uv run python -c "import os; print(os.getenv('DEBUG'))"
   ```

## Service URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend Dev | http://localhost:5173 | Vite dev server with HMR |
| Frontend (alt) | http://localhost:3000 | Alternative port |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| WebSocket | ws://localhost:8000/ws/simulation | Real-time updates |
| Health Check | http://localhost:8000/api/health | Service status |
| Status | http://localhost:8000/api/status | Detailed simulation status |

## Development Best Practices

1. **Always run tests before committing**
   ```bash
   cd server && uv run pytest
   cd client && npm test
   ```

2. **Type check frontend code**
   ```bash
   cd client && npm run typecheck
   ```

3. **Keep dependencies updated**
   ```bash
   # Backend
   cd server && uv lock --upgrade

   # Frontend
   cd client && npm update
   ```

4. **Use .env.local for personal settings**
   - Never commit .env.local
   - Document required variables in .env.local.example

5. **Monitor logs during development**
   - Watch for errors and warnings
   - Use appropriate log levels

6. **Clean up regularly**
   ```bash
   # Stop services
   ./scripts/dev.sh --down

   # Clean Docker
   docker system prune

   # Clean Python caches
   find . -type d -name __pycache__ -exec rm -r {} +
   ```

## Next Steps

- Read [CLAUDE.md](./CLAUDE.md) for AI assistant guidelines
- Review [README.md](./README.md) for project overview
- Check [scripts/README.md](./scripts/README.md) for script details
- Explore the codebase architecture in CLAUDE.md

Happy coding! 🚀
