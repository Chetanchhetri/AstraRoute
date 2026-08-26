from fastapi import APIRouter
from app.services.weather_service import get_weather

router = APIRouter()

@router.get("/forecast")
def forecast(latitude: float, longitude: float):
    return get_weather(latitude, longitude)
