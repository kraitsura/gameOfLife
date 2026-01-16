# Backend Resilience Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to improve the resilience and robustness of the Game of Life backend server, addressing critical issues with process management, WebSocket stability, and production deployment.

**Current Issues Identified:**
- Orphaned uvicorn processes when dev script is terminated
- Multi-worker configuration breaks WebSocket state sharing
- Limited error recovery in WebSocket broadcast loop
- Weak simulation loop error handling
- Missing graceful shutdown mechanisms

**Goal:** Create a production-ready backend that can run indefinitely on a VPS with automatic recovery from common failure scenarios.

---

## Phase 1: Fix Critical Multi-Worker Issue ⚠️

**Priority:** CRITICAL
**Estimated Effort:** 2-3 hours
**Risk:** HIGH - Current production deployment is fundamentally broken

### Problem Analysis

The production Dockerfile (`server/Dockerfile:22`) uses `--workers 4`, which spawns 4 separate uvicorn worker processes. However, the application stores WebSocket state in memory:

```python
# main.py:25-26
app.state.simulation = SimulationManager(...)
app.state.active_connections = set()
```

This creates multiple problems:
1. Each worker has its own simulation instance (4 separate simulations)
2. WebSocket connections only exist in one worker's memory
3. broadcast_state task in one worker can't access connections in other workers
4. Clients randomly connect to different workers, causing state desync

### Implementation Tasks

#### 1.1 Update Production Dockerfile
**File:** `server/Dockerfile`

Remove multi-worker configuration:
```dockerfile
# OLD (line 22):
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# NEW:
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--loop", "uvloop", "--timeout-keep-alive", "75"]
```

**Rationale:**
- Single process maintains shared state
- `--loop uvloop` provides async performance boost (10-20% faster)
- `--timeout-keep-alive 75` matches nginx keepalive settings

#### 1.2 Update docker-compose.yml
**File:** `docker-compose.yml`

Remove worker-related environment variables and add resource limits:
```yaml
backend:
  # ... existing config ...
  environment:
    - CORS_ORIGINS=["http://localhost", "https://simulation.aaryareddy.com"]
    # REMOVE: UVICORN_WORKERS, MAX_WORKERS
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
```

#### 1.3 Add uvloop Dependency
**File:** `server/pyproject.toml`

```bash
cd server
uv add uvloop
```

### Verification

After deployment:
1. Check only one uvicorn process is running: `docker exec backend ps aux | grep uvicorn`
2. Test WebSocket persistence across page refreshes
3. Monitor memory usage (should be stable around 500MB-1GB)

---

## Phase 2: Improve Process Management

**Priority:** HIGH
**Estimated Effort:** 3-4 hours
**Risk:** MEDIUM

### 2.1 Enhanced dev-native.sh Script

**File:** `scripts/dev-native.sh`

#### Issues to Fix:
1. Orphaned processes when script is killed (no proper cleanup)
2. Port conflicts not detected before starting
3. Cleanup trap doesn't always execute
4. Kill signals don't propagate to child processes

#### Implementation

**Add PID file management:**
```bash
# After line 24
PID_DIR="scripts/pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# After line 48
mkdir -p "$PID_DIR"
```

**Add port availability check:**
```bash
# After line 72 (after prerequisites check)
echo -e "${BLUE}Checking port availability...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port 8000 is already in use${NC}"
    echo "Processes using port 8000:"
    lsof -i :8000
    echo ""
    echo "Kill with: kill -9 \$(lsof -t -i:8000)"
    exit 1
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 5173 is already in use${NC}"
    echo "Frontend may fail to start"
fi

echo -e "${GREEN}✓ Ports available${NC}"
echo ""
```

**Improve cleanup with process groups:**
```bash
# Replace cleanup function (lines 26-42)
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"

    # Kill backend process group
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "Stopping backend (PID: $BACKEND_PID)..."
            # Kill process group (-PID sends to entire group)
            kill -TERM -$BACKEND_PID 2>/dev/null || true

            # Wait up to 5 seconds for graceful shutdown
            for i in {1..5}; do
                if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if ps -p $BACKEND_PID > /dev/null 2>&1; then
                echo "Force killing backend..."
                kill -9 -$BACKEND_PID 2>/dev/null || true
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    # Kill frontend process group (similar logic)
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "Stopping frontend (PID: $FRONTEND_PID)..."
            kill -TERM -$FRONTEND_PID 2>/dev/null || true

            for i in {1..5}; do
                if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done

            if ps -p $FRONTEND_PID > /dev/null 2>&1; then
                echo "Force killing frontend..."
                kill -9 -$FRONTEND_PID 2>/dev/null || true
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # Cleanup any remaining orphaned processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true

    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}
```

**Update process starting to use process groups:**
```bash
# Replace line 105
set -m  # Enable job control for process groups
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "../$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../$BACKEND_PID_FILE"
set +m
```

### 2.2 Add Startup Recovery Script

**New File:** `scripts/cleanup-dev.sh`

```bash
#!/bin/bash
# cleanup-dev.sh - Force cleanup of development processes

set -e

echo "Cleaning up development processes..."

# Kill uvicorn processes
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "Killing uvicorn processes..."
    pkill -9 -f "uvicorn app.main:app" || true
fi

# Kill vite/npm processes
if pgrep -f "vite" > /dev/null; then
    echo "Killing vite processes..."
    pkill -9 -f "vite" || true
fi

# Clean PID files
rm -f scripts/pids/*.pid

# Clean log files (optional)
# rm -f scripts/logs/*.log

echo "Cleanup complete. You can now run ./scripts/dev-native.sh"
```

Make executable:
```bash
chmod +x scripts/cleanup-dev.sh
```

---

## Phase 3: Backend Resilience Enhancements

**Priority:** HIGH
**Estimated Effort:** 4-6 hours
**Risk:** MEDIUM

### 3.1 Improve WebSocket Broadcast Resilience

**File:** `server/app/main.py`

#### Add connection limits and rate limiting

**After line 11:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

# Configuration constants
MAX_CONNECTIONS = 100
CONNECTION_RATE_LIMIT = 10  # connections per minute per IP
BROADCAST_ERROR_THRESHOLD = 10  # consecutive errors before backoff
```

**Add connection tracking (after line 25):**
```python
app.state.active_connections = set()
app.state.connection_attempts = defaultdict(list)  # IP -> [timestamp, ...]
app.state.broadcast_error_count = 0
```

#### Enhanced broadcast_state with exponential backoff

**Replace broadcast_state function (lines 118-148):**
```python
async def broadcast_state(simulation: SimulationManager,
                         active_connections: Set[WebSocket]) -> None:
    """Broadcast simulation state to all connected clients with error recovery."""
    error_count = 0
    backoff_delay = 1/60  # Start at 60 FPS
    max_backoff = 5.0  # Max 5 seconds between broadcasts

    while True:
        try:
            if active_connections:
                state = simulation.get_state()

                # Check if simulation state is valid
                if "error" in state:
                    logging.error(f"Simulation state error: {state['error']}")
                    error_count += 1
                    await asyncio.sleep(min(backoff_delay * (2 ** error_count), max_backoff))
                    continue

                # Send to each connection individually with error handling
                stale_connections = set()
                send_errors = 0

                for connection in list(active_connections):
                    try:
                        # Check if connection is still open before sending
                        if connection.client_state.name != "CONNECTED":
                            stale_connections.add(connection)
                            continue

                        await asyncio.wait_for(
                            connection.send_json(state),
                            timeout=0.1  # 100ms timeout per send
                        )
                    except asyncio.TimeoutError:
                        logging.warning("Send timeout for connection, marking as stale")
                        stale_connections.add(connection)
                        send_errors += 1
                    except Exception as e:
                        logging.warning(f"Failed to send to connection: {e}")
                        stale_connections.add(connection)
                        send_errors += 1

                # Remove stale connections
                if stale_connections:
                    active_connections -= stale_connections
                    logging.info(f"Removed {len(stale_connections)} stale connection(s)")

                # Reset error count on successful broadcast
                if send_errors == 0:
                    error_count = 0
                    backoff_delay = 1/60
                else:
                    error_count = min(error_count + 1, 5)
                    backoff_delay = min(1/60 * (2 ** error_count), max_backoff)

            await asyncio.sleep(backoff_delay)

        except Exception as e:
            error_count += 1
            backoff_delay = min(1/60 * (2 ** error_count), max_backoff)
            logging.error(f"Broadcast error (count: {error_count}): {e}", exc_info=True)
            await asyncio.sleep(backoff_delay)

            # Circuit breaker: if too many errors, pause and alert
            if error_count > BROADCAST_ERROR_THRESHOLD:
                logging.critical(f"Broadcast has failed {error_count} times, entering degraded mode")
                await asyncio.sleep(30)  # Long backoff
                error_count = BROADCAST_ERROR_THRESHOLD  # Cap error count
```

#### Add connection rate limiting

**Add before websocket_endpoint (after line 148):**
```python
def check_rate_limit(client_ip: str, connection_attempts: dict) -> bool:
    """Check if client IP is within rate limit."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)

    # Clean old attempts
    connection_attempts[client_ip] = [
        ts for ts in connection_attempts[client_ip] if ts > cutoff
    ]

    # Check limit
    if len(connection_attempts[client_ip]) >= CONNECTION_RATE_LIMIT:
        return False

    connection_attempts[client_ip].append(now)
    return True
```

#### Update websocket_endpoint with limits

**Replace websocket_endpoint (lines 149-247):**
```python
@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    # Rate limiting
    client_ip = websocket.client.host
    if not check_rate_limit(client_ip, app.state.connection_attempts):
        logging.warning(f"Rate limit exceeded for {client_ip}")
        await websocket.close(code=1008, reason="Rate limit exceeded")
        return

    # Connection limit
    if len(app.state.active_connections) >= MAX_CONNECTIONS:
        logging.warning(f"Connection limit reached ({MAX_CONNECTIONS})")
        await websocket.close(code=1008, reason="Server at capacity")
        return

    await websocket.accept()
    app.state.active_connections.add(websocket)
    logging.info(f"Client connected from {client_ip}. Total connections: {len(app.state.active_connections)}")

    heartbeat_interval = 30
    last_heartbeat = time.time()
    last_pong = time.time()

    try:
        # Send initial state with error handling
        try:
            state = app.state.simulation.get_state()
            await asyncio.wait_for(
                websocket.send_json(state),
                timeout=5.0
            )
            logging.debug("Sent initial state with %d entities", len(state.get("entities", {})))
        except asyncio.TimeoutError:
            logging.error("Timeout sending initial state")
            raise
        except WebSocketDisconnect:
            logging.debug("Client disconnected before receiving initial state")
            raise
        except Exception as e:
            logging.error("Failed to send initial state: %s", str(e), exc_info=True)
            raise

        while True:
            # Heartbeat check
            if time.time() - last_heartbeat > heartbeat_interval:
                try:
                    await websocket.send_json({"type": "ping"})
                    last_heartbeat = time.time()
                except Exception as e:
                    logging.warning(f"Failed to send heartbeat: {e}")
                    break

            # Pong timeout check (client must respond within 60s)
            if time.time() - last_pong > 60:
                logging.warning("Client failed to respond to heartbeat, closing connection")
                break

            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)

                if data["type"] == "pong":
                    last_pong = time.time()
                elif data["type"] == "start":
                    await app.state.simulation.start()
                elif data["type"] == "pause":
                    await app.state.simulation.pause()
                elif data["type"] == "add_species":
                    try:
                        # ... existing add_species logic ...
                        particle_type = data.get("rules", {}).get("particleType", "creature")
                        entity_type = EntityType.PLANT if particle_type == "plant" else EntityType.CREATURE

                        base_traits = set()
                        if "diet" in data:
                            base_traits.add(Trait(data["diet"]))
                        if "reproductionStyle" in data:
                            base_traits.add(Trait(data["reproductionStyle"]))

                        initial_count = data.get("initialCount", 10)
                        species_name = data.get("name", "Unnamed Species")
                        species_color = data.get("color", "#FFFFFF")

                        logging.info(
                            f"Adding species '{species_name}' with {initial_count} entities, "
                            f"type={entity_type.value}, traits={[t.value for t in base_traits]}"
                        )

                        app.state.simulation.add_species(
                            name=species_name,
                            color=species_color,
                            entity_type=entity_type,
                            base_traits=base_traits,
                            initial_count=initial_count
                        )

                        await websocket.send_json({
                            "type": "species_added",
                            "name": species_name,
                            "count": initial_count
                        })
                    except ValueError as e:
                        logging.error(f"Invalid species data: {e}")
                        await websocket.send_json({"error": f"Invalid species data: {e}"})

            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logging.error("Error processing websocket message: %s", str(e))
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception:
                    pass

    except WebSocketDisconnect as e:
        logging.info(f"Client {client_ip} disconnected normally")
    except Exception as e:
        logging.error(f"Websocket error for {client_ip}: {e}", exc_info=True)
    finally:
        # Always remove connection on exit
        if websocket in app.state.active_connections:
            app.state.active_connections.remove(websocket)
            logging.info(
                f"Removed connection from {client_ip}. "
                f"{len(app.state.active_connections)} active connection(s) remaining"
            )
```

### 3.2 Add Graceful Shutdown Handler

**File:** `server/app/main.py`

**Add after imports (line 16):**
```python
import signal
from contextlib import asynccontextmanager
```

**Update lifespan manager (replace lines 18-51):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting application...")

    app.state.simulation = SimulationManager(
        world_width=WORLD_CONFIG["WIDTH"],
        world_height=WORLD_CONFIG["HEIGHT"]
    )
    app.state.active_connections = set()
    app.state.connection_attempts = defaultdict(list)
    app.state.is_shutting_down = False

    # Add initial species
    await setup_initial_species(app.state.simulation)

    # Auto-start the simulation
    await app.state.simulation.start()
    logging.info("Simulation auto-started")

    # Start the broadcast task for WebSocket updates at 60 FPS
    app.state.broadcast_task = asyncio.create_task(
        broadcast_state(app.state.simulation, app.state.active_connections)
    )
    logging.info("Broadcast task started - clients will receive 60 FPS updates")

    # Setup signal handlers for graceful shutdown
    def handle_shutdown_signal(signum, frame):
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        app.state.is_shutting_down = True

    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    yield

    # Shutdown
    logging.info("Shutting down application...")
    app.state.is_shutting_down = True

    # Stop accepting new connections (notify existing ones)
    disconnect_tasks = []
    for connection in list(app.state.active_connections):
        async def notify_and_close(conn):
            try:
                await conn.send_json({"type": "server_shutdown", "message": "Server is shutting down"})
                await asyncio.sleep(0.1)
                await conn.close()
            except Exception:
                pass

        disconnect_tasks.append(notify_and_close(connection))

    # Wait for all disconnections (with timeout)
    if disconnect_tasks:
        await asyncio.wait_for(
            asyncio.gather(*disconnect_tasks, return_exceptions=True),
            timeout=5.0
        )

    # Stop simulation
    if app.state.simulation.is_running:
        await app.state.simulation.pause()
        logging.info("Simulation stopped")

    # Cancel broadcast task
    if app.state.broadcast_task:
        app.state.broadcast_task.cancel()
        try:
            await app.state.broadcast_task
        except asyncio.CancelledError:
            pass
        logging.info("Broadcast task cancelled")

    logging.info("Shutdown complete")
```

### 3.3 Simulation Loop Error Handling

**File:** `server/app/simulation/simulation.py`

**Add circuit breaker constants (after line 10):**
```python
# Circuit breaker configuration
MAX_CONSECUTIVE_ERRORS = 5
ERROR_RESET_TIME = 60  # seconds
```

**Update SimulationManager.__init__ (add after line 25):**
```python
self.consecutive_errors = 0
self.last_error_time = 0
self.is_degraded = False  # Circuit breaker state
```

**Replace _update_loop (lines 42-64):**
```python
async def _update_loop(self) -> None:
    """Main update loop running asynchronously with error recovery."""
    while self._is_running:
        try:
            current_time = time.time()
            frame_time = current_time - self.last_update_time
            self.last_update_time = current_time

            # Reset error counter if enough time has passed since last error
            if self.consecutive_errors > 0 and (current_time - self.last_error_time) > ERROR_RESET_TIME:
                logging.info(f"Resetting error counter after {ERROR_RESET_TIME}s of stable operation")
                self.consecutive_errors = 0
                self.is_degraded = False

            self.accumulator += frame_time

            while self.accumulator >= self.fixed_dt:
                try:
                    # Spawn random plants each tick (10% chance)
                    if self.plant_species_id and random.random() < self.plant_spawn_rate:
                        self._spawn_random_plant()

                    self.world.update(self.fixed_dt)

                    # Clean up any out-of-bounds entities
                    self._cleanup_out_of_bounds_entities()

                    self.accumulator -= self.fixed_dt

                except Exception as e:
                    logging.error(f"Error during simulation update: {e}", exc_info=True)
                    self.consecutive_errors += 1
                    self.last_error_time = current_time

                    # Circuit breaker: stop simulation if too many errors
                    if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logging.critical(
                            f"Simulation has failed {self.consecutive_errors} times, "
                            f"entering degraded mode"
                        )
                        self.is_degraded = True
                        self._is_running = False
                        break

                    # Skip this update and continue
                    self.accumulator = 0
                    break

            # Allow other tasks to run
            await asyncio.sleep(0.01)

        except Exception as e:
            # Catch-all for unexpected errors in the loop itself
            logging.critical(f"Critical error in update loop: {e}", exc_info=True)
            self.consecutive_errors += 1
            self.last_error_time = time.time()

            if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logging.critical("Too many critical errors, stopping simulation")
                self._is_running = False
                break

            # Backoff before retrying
            await asyncio.sleep(min(2 ** self.consecutive_errors, 30))

    if self.is_degraded:
        logging.warning("Simulation loop exited in degraded state")
```

**Add recovery method:**
```python
async def recover(self) -> bool:
    """Attempt to recover from degraded state."""
    if not self.is_degraded:
        return True

    logging.info("Attempting to recover simulation from degraded state...")
    self.consecutive_errors = 0
    self.is_degraded = False

    try:
        # Reset simulation time tracking
        self.last_update_time = time.time()
        self.accumulator = 0.0

        # Restart
        await self.start()
        logging.info("Simulation recovered successfully")
        return True
    except Exception as e:
        logging.error(f"Recovery failed: {e}")
        self.is_degraded = True
        return False
```

**Update get_state to include error info (line 121):**
```python
def get_state(self) -> dict:
    """Return the current state of the simulation."""
    try:
        # ... existing code ...

        state = {
            "entities": {str(entity.id): entity.serialize() for entity in entities},
            "species": {str(sp.id): sp.serialize() for sp in species},
            "packs": {str(pack.id): pack.serialize() for pack in packs} if packs else {},
            "worldWidth": self.world.width,
            "worldHeight": self.world.height,
            "tickRate": self.world.tick_rate,
            "isRunning": self._is_running,
            "isDegraded": self.is_degraded,  # NEW
            "consecutiveErrors": self.consecutive_errors  # NEW
        }

        return state
    except Exception as e:
        logging.error("Error getting simulation state: %s", str(e))
        return {"error": f"Failed to get simulation state: {str(e)}"}
```

---

## Phase 4: Docker Production Hardening

**Priority:** MEDIUM
**Estimated Effort:** 2-3 hours
**Risk:** LOW

### 4.1 Update Production Dockerfile

**File:** `server/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        tini && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies using uv (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run application with optimized settings
CMD ["uv", "run", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--loop", "uvloop", \
     "--timeout-keep-alive", "75", \
     "--timeout-graceful-shutdown", "30"]

EXPOSE 8000
```

**Key improvements:**
- `tini` as PID 1 for proper signal forwarding
- `--timeout-graceful-shutdown 30` gives app time to cleanup
- Single worker (removed --workers flag)
- uvloop for better async performance

### 4.2 Enhanced Health Checks

**File:** `docker-compose.yml`

```yaml
backend:
  # ... existing config ...
  healthcheck:
    test: |
      curl -f http://localhost:8000/api/health && \
      curl -f http://localhost:8000/api/status | grep -q '"status":"healthy"'
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  restart: unless-stopped
  stop_grace_period: 30s
```

**Update health endpoint (server/app/main.py):**
```python
@app.get("/api/health")
async def health_check():
    """Health check endpoint with degraded state detection."""
    if app.state.is_shutting_down:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "shutting_down"}
        )

    # Check simulation state
    if hasattr(app.state, 'simulation') and app.state.simulation.is_degraded:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "message": "Simulation is in degraded state",
                "consecutive_errors": app.state.simulation.consecutive_errors
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"}
    )
```

### 4.3 Add Restart Policies

**File:** `docker-compose.yml`

```yaml
backend:
  # ... existing config ...
  restart: unless-stopped
  deploy:
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 3
      window: 120s
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
```

---

## Phase 5: Monitoring & Observability

**Priority:** MEDIUM
**Estimated Effort:** 3-4 hours
**Risk:** LOW

### 5.1 Structured Logging

**File:** `server/app/main.py`

**Add logging configuration (after imports):**
```python
import sys
import json
from datetime import datetime

# Configure structured logging
class StructuredLogger:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            **kwargs
        }

        if os.getenv("ENVIRONMENT") == "production":
            # JSON logging for production
            self.logger.info(json.dumps(log_entry))
        else:
            # Human-readable for development
            extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self.logger.info(f"[{level}] {message} {extras}")

    def info(self, message: str, **kwargs):
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("ERROR", message, **kwargs)

# Replace standard logging
app_logger = StructuredLogger("app")
```

### 5.2 Enhanced Status Endpoint

**File:** `server/app/main.py`

**Replace `/api/status` endpoint (lines 257-278):**
```python
@app.get("/api/status")
async def simulation_status():
    """Get detailed simulation status with metrics."""
    try:
        state = app.state.simulation.get_state()

        # Calculate uptime
        import psutil
        process = psutil.Process()
        uptime_seconds = time.time() - process.create_time()

        return {
            "status": "degraded" if app.state.simulation.is_degraded else "healthy",
            "uptime_seconds": int(uptime_seconds),
            "simulation": {
                "active": app.state.simulation.is_running,
                "degraded": app.state.simulation.is_degraded,
                "consecutive_errors": app.state.simulation.consecutive_errors,
                "species_count": len(state.get("species", {})),
                "entity_count": len(state.get("entities", {})),
                "pack_count": len(state.get("packs", {})),
            },
            "websocket": {
                "active_connections": len(app.state.active_connections),
                "max_connections": MAX_CONNECTIONS,
                "utilization_percent": (len(app.state.active_connections) / MAX_CONNECTIONS) * 100
            },
            "system": {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "threads": process.num_threads()
            }
        }
    except Exception as e:
        logging.error("Status check failed: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "message": str(e)
            }
        )
```

**Add psutil dependency:**
```bash
cd server
uv add psutil
```

### 5.3 WebSocket Lifecycle Logging

**File:** `server/app/main.py`

Add correlation IDs and detailed lifecycle logging throughout the websocket_endpoint function:

```python
import uuid

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    conn_id = str(uuid.uuid4())[:8]  # Short correlation ID
    client_ip = websocket.client.host

    app_logger.info(
        "WebSocket connection attempt",
        conn_id=conn_id,
        client_ip=client_ip,
        active_connections=len(app.state.active_connections)
    )

    # ... existing rate limiting and connection limit code ...

    await websocket.accept()
    app.state.active_connections.add(websocket)

    app_logger.info(
        "WebSocket connected",
        conn_id=conn_id,
        client_ip=client_ip,
        total_connections=len(app.state.active_connections)
    )

    # ... rest of websocket handler ...

    # In finally block:
    finally:
        if websocket in app.state.active_connections:
            app.state.active_connections.remove(websocket)

            app_logger.info(
                "WebSocket disconnected",
                conn_id=conn_id,
                client_ip=client_ip,
                remaining_connections=len(app.state.active_connections)
            )
```

### 5.4 Optional: Prometheus Metrics

**New File:** `server/app/metrics.py`

```python
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from fastapi import Response

# Metrics
websocket_connections = Gauge('websocket_connections', 'Number of active WebSocket connections')
websocket_messages = Counter('websocket_messages_total', 'Total WebSocket messages', ['type'])
simulation_entities = Gauge('simulation_entities', 'Number of entities in simulation', ['species'])
simulation_errors = Counter('simulation_errors_total', 'Total simulation errors')
broadcast_duration = Histogram('broadcast_duration_seconds', 'Time to broadcast state to all clients')

def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
```

**File:** `server/app/main.py`

```python
from app.metrics import get_metrics, websocket_connections, websocket_messages

@app.get("/metrics")
async def metrics():
    return get_metrics()

# Update connection tracking
websocket_connections.set(len(app.state.active_connections))
```

**Add prometheus dependency:**
```bash
cd server
uv add prometheus-client
```

---

## Testing & Validation

### Test Checklist

#### Phase 1 Testing
- [ ] Verify single uvicorn process in production
- [ ] Test WebSocket persistence across multiple page refreshes
- [ ] Load test with 50+ concurrent connections
- [ ] Monitor memory usage over 24 hours

#### Phase 2 Testing
- [ ] Test dev-native.sh startup and shutdown
- [ ] Test Ctrl+C cleanup (no orphaned processes)
- [ ] Test port conflict detection
- [ ] Test cleanup-dev.sh recovery script

#### Phase 3 Testing
- [ ] Test connection rate limiting (>10 conn/min from one IP)
- [ ] Test max connection limit (>100 connections)
- [ ] Test graceful shutdown with active connections
- [ ] Simulate simulation errors and verify circuit breaker
- [ ] Test simulation recovery endpoint

#### Phase 4 Testing
- [ ] Test Docker graceful shutdown (SIGTERM)
- [ ] Test health check endpoints
- [ ] Test restart policies with simulated failures
- [ ] Verify resource limits under load

#### Phase 5 Testing
- [ ] Verify structured logging in production
- [ ] Test /api/status endpoint metrics
- [ ] Test Prometheus metrics (if implemented)
- [ ] Verify WebSocket lifecycle logging

---

## Rollout Strategy

### Development Environment
1. Implement Phase 2 first (dev-native.sh improvements)
2. Test locally for 1-2 days
3. Implement Phase 3 (backend resilience)
4. Test with simulated errors

### Production Environment
1. Implement Phase 1 (critical worker fix)
2. Deploy during low-traffic window
3. Monitor for 24 hours
4. Roll out Phases 3-4 incrementally
5. Add Phase 5 monitoring last

---

## Appendix: Common Issues & Solutions

### Issue: Orphaned uvicorn processes
**Solution:** Use cleanup-dev.sh script or manually:
```bash
pkill -9 -f "uvicorn app.main:app"
```

### Issue: Port 8000 already in use
**Solution:** Script now detects this automatically. Manual fix:
```bash
lsof -ti :8000 | xargs kill -9
```

### Issue: WebSocket disconnects randomly
**Solution:** Phase 1 fixes worker issue, Phase 3 adds better error handling

### Issue: Simulation enters degraded mode
**Solution:** Check logs for errors, use recovery endpoint:
```bash
curl -X POST http://localhost:8000/api/simulation/recover
```

---

## References

- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Docker Signal Handling](https://docs.docker.com/engine/reference/run/#stop-container)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
