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

# Lifespan context manager for proper startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.simulation = SimulationManager(world_width=800, world_height=600)
    app.state.active_connections = set()
    app.state.broadcast_task = None
    
    # Add initial species
    await setup_initial_species(app.state.simulation)
    
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
    """Set up initial species in the simulation."""
    simulation.add_species(
        name="Plants",
        color="#2ECC71",
        entity_type=EntityType.PLANT,
        base_traits={Trait.SELF_REPLICATING},
        initial_count=50
    )
    simulation.add_species(
        name="Herbivores",
        color="#2ECC71",
        entity_type=EntityType.CREATURE,
        base_traits={Trait.HERBIVORE, Trait.TWO_PARENTS},
        initial_count=50
    )
    simulation.add_species(
        name="Carnivores",
        color="#E74C3C",
        entity_type=EntityType.CREATURE,
        base_traits={Trait.CARNIVORE, Trait.TWO_PARENTS},
        initial_count=50
    )
    simulation.add_species(
        name="Omnivores",
        color="#F39C12",
        entity_type=EntityType.CREATURE,
        base_traits={Trait.OMNIVORE, Trait.TWO_PARENTS},
        initial_count=50
    )

async def broadcast_state(simulation: SimulationManager, 
                         active_connections: Set[WebSocket]) -> None:
    """Broadcast simulation state to all connected clients."""
    while True:
        try:
            if active_connections:
                state = simulation.get_state()
                await asyncio.gather(
                    *[connection.send_json(state) for connection in active_connections],
                    return_exceptions=True
                )
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
        await websocket.send_json(app.state.simulation.get_state())
        
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
                    app.state.simulation.add_species(
                        name=data["name"],
                        color=data["color"],
                        rules=data["rules"],
                        diet=Trait(data["diet"]),
                        reproduction_style=Trait(data["reproductionStyle"]),
                        initial_count=data.get("initialCount", 10)
                    )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error("Error processing websocket message: %s", str(e))
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        app.state.active_connections.remove(websocket)
    except Exception as e:
        logging.error("Websocket error: %s", str(e))
        if websocket in app.state.active_connections:
            app.state.active_connections.remove(websocket)

@app.on_event("startup")
async def start_broadcast():
    app.state.broadcast_task = asyncio.create_task(
        broadcast_state(app.state.simulation, app.state.active_connections)
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