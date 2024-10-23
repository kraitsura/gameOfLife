from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Circular Life Simulation"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Simulation settings
    SIMULATION_FPS: int = 60
    WORLD_WIDTH: int = 1000
    WORLD_HEIGHT: int = 1000
    
    # Initial species configurations
    INITIAL_SPECIES: List[dict] = [
        {
            "name": "Herbivore",
            "behavior_type": "HERBIVORE",
            "initial_count": 20,
            "base_attributes": {
                "reproductionRate": 60,
                "hunger": 40,
                "size": 30,
                "socialActivity": 70
            }
        },
        {
            "name": "Predator",
            "behavior_type": "PREDATOR",
            "initial_count": 10,
            "base_attributes": {
                "reproductionRate": 30,
                "hunger": 70,
                "size": 60,
                "socialActivity": 40
            }
        }
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()