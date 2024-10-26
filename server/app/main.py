# server/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Set, Dict

from app.simulation.simulation_manager import SimulationManager
from app.models.simulation import (
    ParticleRules, 
    ParticleType,
    Diet,
    ReproductionStyle
)

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
        if active_connections:  # Only broadcast if there are connections
            try:
                state = simulation.get_state()
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
                    diet=Diet(data["diet"]),
                    reproductionStyle=ReproductionStyle(data["reproductionStyle"]),
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
