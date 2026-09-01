import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OSM Route Optimization API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "route_planner_db")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret_key_change_in_prod")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    PEPPER_KEY: str = os.getenv("PEPPER_KEY", "default_pepper_key")
    
    OSRM_BASE_URL: str = os.getenv("OSRM_BASE_URL", "http://router.project-osrm.org")

    class Config:
        env_file = ".env"

settings = Settings()