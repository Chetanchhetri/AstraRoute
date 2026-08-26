import requests
from app.core.config import settings

def get_weather(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "timezone": "auto",
    }
    response = requests.get(settings.open_meteo_url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()
