# Development Scripts

This directory contains helper scripts for local development.

## Available Scripts

### `dev.sh` - Docker-based Development

Start the development environment using Docker Compose with hot reloading.

**Usage:**
```bash
./scripts/dev.sh [OPTIONS]
```

**Options:**
- `--backend-only` - Start only the backend service (useful when running frontend natively)
- `--logs` - Follow logs after starting services
- `--build` - Force rebuild containers before starting
- `--down` - Stop and remove all development containers
- `--help` - Show help message

**Examples:**
```bash
# Start all services (backend + frontend)
./scripts/dev.sh

# Start backend only with logs
./scripts/dev.sh --backend-only --logs

# Rebuild and start
./scripts/dev.sh --build

# Stop all services
./scripts/dev.sh --down
```

**Features:**
- ✅ Hot reloading for both frontend and backend
- ✅ Automatic health checks
- ✅ Volume mounts for source code
- ✅ Isolated from production setup
- ✅ Faster with uv caching

### `dev-native.sh` - Native Development

Run both frontend and backend natively without Docker.

**Prerequisites:**
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [bun](https://bun.sh) or [npm](https://nodejs.org) - JavaScript runtime

**Usage:**
```bash
./scripts/dev-native.sh
```

**Features:**
- ✅ Fastest hot reloading
- ✅ Direct access to processes
- ✅ Lower resource usage
- ✅ Automatic dependency installation
- ✅ Combined log output
- ✅ Clean shutdown on Ctrl+C

**Logs are saved to:**
- Backend: `scripts/logs/backend.log`
- Frontend: `scripts/logs/frontend.log`

## Which Script Should I Use?

| Scenario | Recommended Script |
|----------|-------------------|
| Quick start, everything in Docker | `dev.sh` |
| Backend in Docker, frontend native | `dev.sh --backend-only` + `cd client && npm run dev` |
| Fastest development experience | `dev-native.sh` |
| Testing Docker builds | `dev.sh --build` |
| CI/CD simulation | `dev.sh` |

## Environment Configuration

Both scripts use:
- `.env.development` - Shared development configuration
- `.env.local` - Personal overrides (gitignored)

Copy `.env.local.example` to `.env.local` to customize.

## Service URLs

Once started, services are available at:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| WebSocket | ws://localhost:8000/ws/simulation |
| Health Check | http://localhost:8000/api/health |
| Status | http://localhost:8000/api/status |

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker compose -f docker-compose.dev.yml logs backend
# Or for native
tail -f scripts/logs/backend.log
```

### Port already in use
```bash
# Find what's using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Dependencies out of sync
```bash
# Docker: Rebuild
./scripts/dev.sh --build

# Native: Resync
cd server && uv sync
cd client && npm install
```

### Hot reload not working
- **Docker**: Check volume mounts in `docker-compose.dev.yml`
- **Native**: Ensure file watchers aren't exceeded (`sysctl fs.inotify.max_user_watches` on Linux)

## Development Workflow

1. **Start services:**
   ```bash
   ./scripts/dev.sh  # or dev-native.sh
   ```

2. **Make changes:**
   - Edit files in `server/app/` or `client/src/`
   - Changes auto-reload

3. **View logs:**
   ```bash
   # Docker
   docker compose -f docker-compose.dev.yml logs -f backend

   # Native
   tail -f scripts/logs/backend.log
   ```

4. **Run tests:**
   ```bash
   # Backend
   cd server && uv run pytest

   # Frontend
   cd client && npm test
   ```

5. **Stop services:**
   ```bash
   # Docker
   ./scripts/dev.sh --down

   # Native
   Ctrl+C (in the terminal running dev-native.sh)
   ```

## Additional Commands

### Access backend shell (Docker)
```bash
docker compose -f docker-compose.dev.yml exec backend bash
```

### Restart specific service (Docker)
```bash
docker compose -f docker-compose.dev.yml restart backend
```

### View all running containers
```bash
docker compose -f docker-compose.dev.yml ps
```

### Clean up everything
```bash
./scripts/dev.sh --down
docker volume prune  # Remove unused volumes
```
