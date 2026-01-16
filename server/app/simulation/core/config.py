from typing import Final

WORLD_CONFIG: Final = {
    "WIDTH": 1600,
    "HEIGHT": 900,
    "TICK_RATE": 1/60,
    "PLANT_SPAWN_RATE": 0.1
}

PHYSICS_CONFIG: Final = {
    "MAX_VELOCITY": 10.0,
    "FRICTION": 0.1,
    "COLLISION_DISTANCE": 5.0,
    "VISION_RANGE": 50.0,
    "INTERACTION_RANGE": 10.0,
    "MAX_FORCE": 5.0,  # Maximum steering force
    "SEPARATION_RADIUS": 15.0,  # Distance to maintain from others
    "WANDER_STRENGTH": 2.0,  # Strength of random wander behavior
    "BOUNCE_DAMPING": 0.8  # Velocity reduction on wall collision (0.8 = 20% energy loss)
}

VITALITY_CONFIG: Final = {
    "BASE_ENERGY": 100.0,
    "ENERGY_DECAY_RATE": 0.2,  # Balanced rate: creatures survive ~8 seconds without food
    "HUNGER_RATE": 0.1,  # Hunger increases when energy < 50%
    "REPRODUCTION_THRESHOLD": 75.0  # Lowered to make reproduction more achievable
}

GRID_CONFIG: Final = {
    "CELL_SIZE": 50.0,  # Should match typical vision/interaction range
    "ENABLE_DEBUG": True  # Send grid statistics to frontend for debugging
}