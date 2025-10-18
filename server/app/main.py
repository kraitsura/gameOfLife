# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import asyncio
from typing import Set
import os
import time
import logging
from contextlib import asynccontextmanager

from app.simulation.simulation import SimulationManager
from app.simulation.core.types import EntityType, Trait
from app.simulation.core.config import WORLD_CONFIG

# Lifespan context manager for proper startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.simulation = SimulationManager(
        world_width=WORLD_CONFIG["WIDTH"],
        world_height=WORLD_CONFIG["HEIGHT"]
    )
    app.state.active_connections = set()

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

    yield

    # Shutdown
    if app.state.simulation.is_running:
        await app.state.simulation.pause()
    if app.state.broadcast_task:
        app.state.broadcast_task.cancel()
        try:
            await app.state.broadcast_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

# CORS configuration
CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS', 
    '["http://localhost:3000", "https://your-frontend-domain.com"]'))

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
                         active_connections: Set[WebSocket]) -> None:
    """Broadcast simulation state to all connected clients."""
    while True:
        try:
            if active_connections:
                state = simulation.get_state()
                # Send to each connection individually with error handling
                stale_connections = set()
                for connection in list(active_connections):
                    try:
                        # Check if connection is still open before sending
                        if connection.client_state.name != "CONNECTED":
                            stale_connections.add(connection)
                            continue
                        await connection.send_json(state)
                    except Exception as e:
                        # Connection failed, mark for removal
                        logging.warning(f"Failed to send to connection, marking as stale: {e}")
                        stale_connections.add(connection)

                # Remove stale connections
                if stale_connections:
                    active_connections -= stale_connections
                    logging.debug(f"Removed {len(stale_connections)} stale connection(s)")

            await asyncio.sleep(1/60)
        except Exception as e:
            logging.error("Broadcast error: %s", str(e))
            await asyncio.sleep(1)  # Back off on error

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app.state.active_connections.add(websocket)
    
    heartbeat_interval = 30
    last_heartbeat = time.time()

    try:
        # Send initial state with error handling
        try:
            state = app.state.simulation.get_state()
            await websocket.send_json(state)
            logging.debug("Sent initial state with %d entities", len(state.get("entities", {})))
        except WebSocketDisconnect:
            # Client disconnected before/during initial send (common in React StrictMode dev)
            logging.debug("Client disconnected before receiving initial state")
            raise
        except Exception as e:
            logging.error("Failed to send initial state: %s", str(e), exc_info=True)
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
                    await app.state.simulation.start()
                elif data["type"] == "pause":
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
                # Re-raise to let outer handler deal with it
                raise
            except Exception as e:
                # Only send error for non-disconnect exceptions
                logging.error("Error processing websocket message: %s", str(e))
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception:
                    # Socket might be closed, ignore send errors
                    pass
                
    except WebSocketDisconnect as e:
        logging.debug(f"Client disconnected normally: {e}")
    except Exception as e:
        logging.error(f"Websocket error: {e}", exc_info=True)
    finally:
        # Always remove connection on exit
        if websocket in app.state.active_connections:
            app.state.active_connections.remove(websocket)
            logging.debug(f"Removed connection, {len(app.state.active_connections)} active connection(s) remaining")

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