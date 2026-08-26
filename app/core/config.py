from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    model_path: str = "multitask_weather_nowcaster.pth"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
