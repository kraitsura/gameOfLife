from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Circular Life Simulation"

    # Application
    APP_NAME: str
    ENVIRONMENT: str
    
    # Server
    BACKEND_HOST: str
    BACKEND_PORT: int
    CORS_ORIGINS: str
    DEBUG: bool
    
    # Database
    DATABASE_URL: str
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int
    
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
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"

settings = Settings()

@lru_cache()
def get_settings():
    return Settings()