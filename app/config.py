from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "OSRM Route Optimization API"
    VERSION: str = "1.0.0"
    
    # Database Configuration
    MONGO_URI: str
    MONGO_DB_NAME: str
    
    # Security
    JWT_SECRET_KEY: str = "production_ultra_secure_jwt_secret_key_12345"
    
    # SMTP Email Credentials
    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""

    # OSRM Service URL (ADDED)
    OSRM_BASE_URL: str = "http://router.project-osrm.org"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()