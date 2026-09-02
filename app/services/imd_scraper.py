import logging
from datetime import datetime, timezone
from scrapling import Fetcher

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast?latitude=26.71&longitude=88.43&current=temperature_2m,relative_humidity_2m,rain,showers,snowfall,weather_code,wind_speed_10m&hourly=rain,precipitation_probability"

def scrape_imd_weather_alerts():
    fetcher = Fetcher()
    alerts = []

    try:
        response = fetcher.get(OPEN_METEO_URL)
        if response.status != 200:
            logger.error(f"[WEATHER SCRAPER] Failed to fetch weather data, status: {response.status}")
            return alerts

        data = response.json()
        current = data.get("current", {})
        
        rain_mm = current.get("rain", 0)
        showers_mm = current.get("showers", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        weather_code = current.get("weather_code", 0)

        # Flag hazard if rain/showers > 0 mm OR weather code indicates precipitation/thunderstorms
        is_hazard = rain_mm >= 0.0 or showers_mm >= 0.0 or weather_code >= 50

        if is_hazard:
            alerts.append({
                "title": "Active Weather Watch - North Bengal Corridor",
                "description": f"Precipitation level: {rain_mm + showers_mm} mm | Wind Speed: {wind_speed} km/h | Weather Code: {weather_code}.",
                "source": "Open-Meteo Live API",
                "pub_date": datetime.now(timezone.utc).isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "weather_warning"
            })
            logger.info("[WEATHER SCRAPER] Weather conditions processed and flagged for spatial avoidance.")

        return alerts

    except Exception as e:
        logger.error(f"[WEATHER SCRAPER ERROR] {str(e)}")
        return alerts