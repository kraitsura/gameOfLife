# server/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Set, Dict

from app.simulation.simulation_manager import SimulationManager
from app.models.simulation import ParticleRules

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
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
    # Add example species
    simulation.add_species(
        name="Explorers",
        color="#FF0000",
        rules=ParticleRules(
            reproductionRate=0.001,
            energyConsumption=0.1,
            maxSpeed=2.0,
            visionRange=50.0,
            socialDistance=20.0
        ),
        initial_count=20
    )

    simulation.add_species(
        name="Socializers",
        color="#00FF00",
        rules=ParticleRules(
            reproductionRate=0.002,
            energyConsumption=0.05,
            maxSpeed=1.5,
            visionRange=70.0,
            socialDistance=15.0
        ),
        initial_count=15
    )

    await simulation.start()

# Broadcast state to all clients
async def broadcast_state():
    while True:
        if active_connections:  # Only broadcast if there are connections
            state = simulation.get_state()
            for connection in active_connections.copy():
                try:
                    await connection.send_json(state)
                except:
                    active_connections.remove(connection)
        await asyncio.sleep(1/30)  # 30 FPS update rate

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        # Send initial state
        await websocket.send_json(simulation.get_state())

        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "start":
                await simulation.start()
            elif data["type"] == "pause":
                await simulation.pause()
            elif data["type"] == "add_species":
                simulation.add_species(
                    name=data["name"],
                    color=data["color"],
                    rules=ParticleRules(**data["rules"]),
                    initial_count=data.get("initialCount", 10)
                )

    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Start broadcast task
@app.on_event("startup")
async def start_broadcast():
    asyncio.create_task(broadcast_state())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)