# server/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import asyncio
from typing import Set, Dict
import os
import time

websocket_server_ready = False

from app.simulation.simulation_manager import SimulationManager
from app.models.simulation import (
    ParticleRules, 
    ParticleType,
    Diet,
    ReproductionStyle
)

app = FastAPI()

# Move websocket_server_ready after app initialization
websocket_server_ready = False

# Add this to set ready state during startup
@app.on_event("startup")
async def set_websocket_ready():
    global websocket_server_ready
    websocket_server_ready = True

# Update CORS settings in main.py
CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS', '["http://localhost", "https://simulation.aaryareddy.com", "http://simulation.aaryareddy.com"]'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simulation
simulation = SimulationManager(world_width=800, world_height=600)

# Store active connections
active_connections: Set[WebSocket] = set()

# Add some initial species
@app.on_event("startup")
async def startup_event():
    # Add plants
    simulation.add_species(
        name="Plants",
        color="#2ECC71",
        rules=ParticleRules(
            reproductionRate=0.02,  # Increased reproduction rate
            energyConsumption=0,
            maxSpeed=0,
            visionRange=0,
            socialDistance=10,
            particleType=ParticleType.PLANT
        ),
        diet=Diet.HERBIVORE,
        reproductionStyle=ReproductionStyle.SELF_REPLICATING,
        initial_count=50  # Increased initial count
    )

    # Add herbivores
    simulation.add_species(
        name="Herbivores",
        color="#3498DB",
        rules=ParticleRules(
            reproductionRate=0.001,
            energyConsumption=0.05,  # Reduced energy consumption
            maxSpeed=1.5,  # Slightly reduced speed
            visionRange=60.0,  # Increased vision range
            socialDistance=20.0,
            particleType=ParticleType.CREATURE
        ),
        diet=Diet.HERBIVORE,
        reproductionStyle=ReproductionStyle.TWO_PARENTS,
        initial_count=20
    )

    # Add carnivores
    simulation.add_species(
        name="Carnivores",
        color="#E74C3C",
        rules=ParticleRules(
            reproductionRate=0.0005,
            energyConsumption=0.08,  # Balanced energy consumption
            maxSpeed=2.0,  # Faster than herbivores
            visionRange=80.0,  # Increased vision range
            socialDistance=25.0,
            particleType=ParticleType.CREATURE
        ),
        diet=Diet.CARNIVORE,
        reproductionStyle=ReproductionStyle.SELF_REPLICATING,
        initial_count=8  # Reduced initial count
    )

    # Add omnivores
    simulation.add_species(
        name="Omnivores",
        color="#9B59B6",
        rules=ParticleRules(
            reproductionRate=0.00075,
            energyConsumption=0.06,  # Balanced energy consumption
            maxSpeed=1.8,  # Balanced speed
            visionRange=70.0,  # Balanced vision range
            socialDistance=22.0,
            particleType=ParticleType.CREATURE
        ),
        diet=Diet.OMNIVORE,
        reproductionStyle=ReproductionStyle.TWO_PARENTS,
        initial_count=12  # Balanced initial count
    )

    await simulation.start()

# Broadcast state to all clients
async def broadcast_state():
    while True:
        try:
            state = simulation.get_state()
            if active_connections:  # Only send if there are connections
                await asyncio.gather(
                    *[connection.send_json(state) for connection in active_connections]
                )
        except Exception as e:
            print(f"Broadcast error: {e}")
        await asyncio.sleep(1/60)  # Match simulation tick rate of 60 FPS

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    
    heartbeat_interval = 30  # seconds
    last_heartbeat = time.time()

    try:
        # Send initial state
        await websocket.send_json(simulation.get_state())
        
        # Handle incoming messages
        while True:
            # Handle heartbeat
            if time.time() - last_heartbeat > heartbeat_interval:
                await websocket.send_json({"type": "ping"})
                last_heartbeat = time.time()
            
            # Use receive_json with timeout to prevent blocking
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                
                if data["type"] == "pong":
                    last_heartbeat = time.time()
                elif data["type"] == "start":
                    await simulation.start()
                elif data["type"] == "pause":
                    await simulation.pause()
                elif data["type"] == "add_species":
                    simulation.add_species(
                        name=data["name"],
                        color=data["color"],
                        rules=ParticleRules(**data["rules"]),
                        diet=Diet(data["diet"]),
                        reproductionStyle=ReproductionStyle(data["reproductionStyle"]),
                        initial_count=data.get("initialCount", 10)
                    )
            except asyncio.TimeoutError:
                continue  # No message received, continue to next iteration
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Start broadcast task
@app.on_event("startup")
async def start_broadcast():
    asyncio.create_task(broadcast_state())

@app.get("/health")
async def health_check():
    try:
        # Basic application health check
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "healthy"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "message": str(e)}
        )

@app.websocket("/ws/health")
async def websocket_health_check(websocket: WebSocket):
    try:
        await websocket.accept()
        await websocket.send_text("healthy")
        await websocket.close()
        return True
    except Exception:
        return False

# Optional: Add a separate endpoint for detailed simulation status
@app.get("/status")
async def simulation_status():
    """Detailed status endpoint for monitoring the simulation"""
    try:
        state = simulation.get_state()
        return {
            "status": "healthy",
            "simulation": {
                "active": simulation.is_running(),
                "species_count": len(state["species"]),
                "total_particles": sum(len(species["particles"]) for species in state["species"]),
            },
            "websocket_connections": len(active_connections)
        }
    except Exception as e:
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
