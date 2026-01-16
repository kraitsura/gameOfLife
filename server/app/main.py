# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import msgpack  # Phase 3 optimization
import asyncio
from typing import Set
import os
import time
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration even if already configured
)

# Create logger for this module
logger = logging.getLogger(__name__)

from app.simulation.simulation import SimulationManager
from app.simulation.delta_encoder import DeltaEncoder  # Phase 3 optimization
from app.simulation.core.types import EntityType, Trait
from app.simulation.core.config import WORLD_CONFIG

# Lifespan context manager for proper startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    environment = os.getenv('ENVIRONMENT', 'production')
    logger.info("Starting Game of Life backend (environment: %s)", environment)

    app.state.simulation = SimulationManager(
        world_width=WORLD_CONFIG["WIDTH"],
        world_height=WORLD_CONFIG["HEIGHT"]
    )
    app.state.active_connections = set()

    # Initialize delta encoder for bandwidth optimization (Phase 3)
    app.state.delta_encoder = DeltaEncoder()
    logger.info("Delta encoder initialized for bandwidth optimization")

    # Add initial species
    await setup_initial_species(app.state.simulation)

    # Auto-start the simulation
    await app.state.simulation.start()
    logger.info("Simulation auto-started")

    # Start the broadcast task for WebSocket updates at 60 FPS
    app.state.broadcast_task = asyncio.create_task(
        broadcast_state(app.state.simulation, app.state.active_connections, app.state.delta_encoder)
    )
    logger.info("Broadcast task started - clients will receive delta-encoded updates at 60 FPS")

    yield

    # Shutdown
    logger.info("Shutting down backend...")
    if app.state.simulation.is_running:
        await app.state.simulation.pause()
    if app.state.broadcast_task:
        app.state.broadcast_task.cancel()
        try:
            await app.state.broadcast_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)

# Request logging middleware (debug mode only)
if os.getenv('DEBUG', 'false').lower() == 'true':
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.debug("HTTP Request: %s %s", request.method, request.url.path)
        response = await call_next(request)
        return response

# CORS configuration
CORS_ORIGINS_RAW = os.getenv('CORS_ORIGINS', '["http://localhost:3000", "http://localhost:5173"]')

try:
    CORS_ORIGINS = json.loads(CORS_ORIGINS_RAW)
    logger.info("CORS origins configured: %s", CORS_ORIGINS)
except json.JSONDecodeError as e:
    logger.error("Failed to parse CORS_ORIGINS, using defaults: %s", str(e))
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def setup_initial_species(simulation: SimulationManager) -> None:
    """Set up initial species in the simulation.

    Initial counts can be configured via environment variables:
    - INITIAL_PLANTS (default: 50)
    - INITIAL_HERBIVORES (default: 20)
    - INITIAL_CARNIVORES (default: 8)
    - INITIAL_OMNIVORES (default: 12)

    Default values match the old server implementation.
    """
    # Read initial counts from environment or use defaults (matching old server)
    initial_plants = int(os.getenv("INITIAL_PLANTS", "50"))
    initial_herbivores = int(os.getenv("INITIAL_HERBIVORES", "20"))
    initial_carnivores = int(os.getenv("INITIAL_CARNIVORES", "8"))
    initial_omnivores = int(os.getenv("INITIAL_OMNIVORES", "12"))

    simulation.add_species(
        name="Plants",
        color="#2ECC71",
        entity_type=EntityType.PLANT,
        base_traits={Trait.SELF_REPLICATING},
        initial_count=initial_plants
    )
    simulation.add_species(
        name="Herbivores",
        color="#3498DB",  # Blue for herbivores (distinguish from plants)
        entity_type=EntityType.CREATURE,
        base_traits={Trait.HERBIVORE, Trait.TWO_PARENTS},
        initial_count=initial_herbivores
    )
    simulation.add_species(
        name="Carnivores",
        color="#E74C3C",
        entity_type=EntityType.CREATURE,
        base_traits={Trait.CARNIVORE, Trait.TWO_PARENTS},
        initial_count=initial_carnivores
    )
    simulation.add_species(
        name="Omnivores",
        color="#F39C12",
        entity_type=EntityType.CREATURE,
        base_traits={Trait.OMNIVORE, Trait.TWO_PARENTS},
        initial_count=initial_omnivores
    )

    logging.info(
        f"Initial species configured: {initial_plants} plants, "
        f"{initial_herbivores} herbivores, {initial_carnivores} carnivores, "
        f"{initial_omnivores} omnivores"
    )

async def broadcast_state(simulation: SimulationManager,
                         active_connections: Set[WebSocket],
                         delta_encoder: DeltaEncoder) -> None:
    """
    Broadcast simulation state to all connected clients (Phase 3 optimized).

    Uses delta encoding and MessagePack for bandwidth optimization:
    - Only sends changes (added/modified/removed entities/packs)
    - Binary serialization instead of JSON
    - 4-5x bandwidth reduction
    """
    logging.info("Broadcast task started - clients will receive delta-encoded updates at 60 FPS")
    consecutive_errors = 0
    max_consecutive_errors = 5

    try:
        while True:
            try:
                if active_connections:
                    # Get simulation state
                    try:
                        state = simulation.get_state()
                    except Exception as e:
                        logging.error(
                            "Failed to get simulation state in broadcast loop: %s",
                            str(e),
                            exc_info=True
                        )
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logging.critical(
                                "Too many consecutive state errors (%d), pausing broadcast for recovery",
                                consecutive_errors
                            )
                            await asyncio.sleep(5)
                            consecutive_errors = 0
                        continue

                    # Reset error counter on successful state retrieval
                    consecutive_errors = 0

                    # Encode state as delta (Phase 3 optimization)
                    encoded_state = delta_encoder.encode(state)

                    # Serialize with MessagePack (Phase 3 optimization)
                    try:
                        binary_message = msgpack.packb(encoded_state, use_bin_type=True)
                    except Exception as e:
                        logging.error("Failed to pack message with msgpack: %s", str(e))
                        # Fallback to JSON if msgpack fails
                        binary_message = None

                    # Send to each connection individually with error handling
                    stale_connections = set()
                    successful_sends = 0

                    for connection in list(active_connections):
                        try:
                            if binary_message:
                                # Send binary (MessagePack) message
                                await connection.send_bytes(binary_message)
                            else:
                                # Fallback to JSON
                                await connection.send_json(encoded_state)
                            successful_sends += 1
                        except WebSocketDisconnect:
                            # Client cleanly disconnected
                            logging.debug("WebSocket disconnected during broadcast")
                            stale_connections.add(connection)
                        except RuntimeError as e:
                            # Connection closed or in invalid state
                            if "WebSocket" in str(e) or "close" in str(e).lower():
                                logging.debug("WebSocket connection closed: %s", str(e))
                                stale_connections.add(connection)
                            else:
                                logging.error("Runtime error during broadcast: %s", str(e), exc_info=True)
                                stale_connections.add(connection)
                        except Exception as e:
                            # Unexpected error, log with full trace
                            logging.error(
                                "Unexpected error sending to WebSocket connection: %s",
                                str(e),
                                exc_info=True
                            )
                            stale_connections.add(connection)

                    # Remove stale connections
                    if stale_connections:
                        active_connections -= stale_connections
                        logging.info(
                            "Removed %d stale connection(s), %d successful sends, %d active connection(s) remaining",
                            len(stale_connections),
                            successful_sends,
                            len(active_connections)
                        )

                await asyncio.sleep(1/60)  # 60 FPS

            except asyncio.CancelledError:
                # Broadcast task is being cancelled (normal during shutdown)
                logging.info("Broadcast task cancelled")
                raise

            except Exception as e:
                # Catch-all for unexpected errors in the main loop
                logging.error(
                    "Critical error in broadcast loop: %s",
                    str(e),
                    exc_info=True
                )
                consecutive_errors += 1
                await asyncio.sleep(1)  # Back off on error

    except asyncio.CancelledError:
        logging.info("Broadcast task cancelled gracefully")
    finally:
        logging.info("Broadcast task stopped")

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    # Log incoming WebSocket connection attempt with details
    connection_id = id(websocket)

    # Log connection details and monitor header sizes
    try:
        headers_dict = dict(websocket.headers)

        # Log key headers for security/debugging
        origin = headers_dict.get('origin', 'NOT SET')
        host = headers_dict.get('host', 'NOT SET')
        user_agent = headers_dict.get('user-agent', 'NOT SET')

        logger.info("WebSocket connection from %s (ID: %s)", origin, connection_id)
        logger.debug("User-Agent: %s", user_agent)

        # Calculate total header size for monitoring
        total_header_size = sum(
            len(f"{key}: {value}\r\n".encode('utf-8'))
            for key, value in headers_dict.items()
        )

        # Warn if headers are unusually large (might indicate cookies/extensions)
        if total_header_size > 16384:  # 16KB threshold
            logger.warning(
                "Large WebSocket headers detected: %d bytes (%.2f KB). "
                "This may be due to authentication cookies or browser extensions.",
                total_header_size,
                total_header_size / 1024
            )

            # In development, show which headers are large
            if os.getenv('ENVIRONMENT') == 'development':
                large_headers = [
                    (key, len(f"{key}: {value}\r\n".encode('utf-8')))
                    for key, value in headers_dict.items()
                    if len(f"{key}: {value}\r\n".encode('utf-8')) > 4096  # 4KB threshold
                ]
                if large_headers:
                    logger.debug("Large headers: %s",
                               ", ".join(f"{k} ({v} bytes)" for k, v in large_headers))
        else:
            logger.debug("Total header size: %d bytes", total_header_size)

    except Exception as e:
        logger.error("Failed to process headers: %s", str(e), exc_info=True)

    try:
        await websocket.accept()
        logger.debug("WebSocket accepted (ID: %s)", connection_id)
    except Exception as e:
        logger.error("Failed to accept WebSocket (ID: %s): %s", connection_id, str(e), exc_info=True)
        raise

    app.state.active_connections.add(websocket)
    logger.info("WebSocket connected (ID: %s), %d active", connection_id, len(app.state.active_connections))

    heartbeat_interval = 30
    last_heartbeat = time.time()

    try:
        # Send initial state with error handling (Phase 3: use MessagePack)
        try:
            state = app.state.simulation.get_state()

            # Encode as full state (not delta for initial connection)
            initial_message = {
                'type': 'full',
                'state': state,
                'frame': 0,
                'tick': state.get('tick', 0)
            }

            # Send as binary MessagePack message
            try:
                binary_message = msgpack.packb(initial_message, use_bin_type=True)
                await websocket.send_bytes(binary_message)
            except Exception:
                # Fallback to JSON if MessagePack fails
                await websocket.send_json(initial_message)

            logging.info(
                "Sent initial state to connection %s with %d entities",
                connection_id,
                len(state.get("entities", {}))
            )
        except WebSocketDisconnect:
            # Client disconnected before/during initial send (common in React StrictMode dev)
            logging.info("Client %s disconnected before receiving initial state", connection_id)
            raise
        except Exception as e:
            logging.error(
                "Failed to send initial state to connection %s: %s",
                connection_id,
                str(e),
                exc_info=True
            )
            raise

        while True:
            if time.time() - last_heartbeat > heartbeat_interval:
                await websocket.send_json({"type": "ping"})
                last_heartbeat = time.time()

            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)

                if data["type"] == "pong":
                    last_heartbeat = time.time()
                elif data["type"] == "start":
                    logging.info("Connection %s requested simulation start", connection_id)
                    await app.state.simulation.start()
                elif data["type"] == "pause":
                    logging.info("Connection %s requested simulation pause", connection_id)
                    await app.state.simulation.pause()
                elif data["type"] == "add_species":
                    try:
                        # Map legacy frontend format to new ECS backend
                        # Extract entity_type from rules.particleType
                        particle_type = data.get("rules", {}).get("particleType", "creature")
                        entity_type = EntityType.PLANT if particle_type == "plant" else EntityType.CREATURE

                        # Build base_traits set from diet and reproductionStyle
                        base_traits = set()
                        if "diet" in data:
                            base_traits.add(Trait(data["diet"]))
                        if "reproductionStyle" in data:
                            base_traits.add(Trait(data["reproductionStyle"]))

                        initial_count = data.get("initialCount", 10)
                        species_name = data.get("name", "Unnamed Species")
                        species_color = data.get("color", "#FFFFFF")

                        logging.info(
                            "Connection %s adding species '%s' with %d entities, type=%s, traits=%s",
                            connection_id,
                            species_name,
                            initial_count,
                            entity_type.value,
                            [t.value for t in base_traits]
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
                        logging.error("Connection %s sent invalid species data: %s", connection_id, str(e))
                        await websocket.send_json({"error": f"Invalid species data: {e}"})
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                # Re-raise to let outer handler deal with it
                raise
            except Exception as e:
                # Only send error for non-disconnect exceptions
                logging.error(
                    "Error processing message from connection %s: %s",
                    connection_id,
                    str(e),
                    exc_info=True
                )
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception:
                    # Socket might be closed, ignore send errors
                    pass

    except WebSocketDisconnect as e:
        logging.info("Connection %s disconnected normally: %s", connection_id, str(e))
    except Exception as e:
        logging.error("WebSocket error for connection %s: %s", connection_id, str(e), exc_info=True)
    finally:
        # Always remove connection on exit
        if websocket in app.state.active_connections:
            app.state.active_connections.remove(websocket)
            logging.info(
                "Removed connection %s, %d active connection(s) remaining",
                connection_id,
                len(app.state.active_connections)
            )

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"}
    )

@app.get("/api/status")
async def simulation_status():
    """Get detailed simulation status."""
    try:
        state = app.state.simulation.get_state()
        return {
            "status": "healthy",
            "simulation": {
                "active": app.state.simulation.is_running,
                "species_count": len(state.get("species", {})),
                "total_particles": len(state.get("particles", {})),
            },
            "websocket_connections": len(app.state.active_connections)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)