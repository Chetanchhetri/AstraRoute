from pydantic import BaseModel, Field
from typing import List, Optional

class Waypoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    name: Optional[str] = "Stop"

class BoundingBox(BaseModel):
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

class WeatherInfo(BaseModel):
    temperature_celsius: float
    weather_condition: str
    wind_speed_kmh: float
    precipitation_probability_percent: int

class WaypointWithWeather(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = "Stop"
    weather: Optional[WeatherInfo] = None

class RouteRequestSchema(BaseModel):
    start: Waypoint
    end: Waypoint
    stops: List[Waypoint] = []
    round_trip: bool = False
    avoid_boxes: List[BoundingBox] = []

class SingleRouteOption(BaseModel):
    title: str
    total_distance_meters: float
    total_duration_seconds: float
    geometry_geojson: dict
    ordered_waypoints: List[WaypointWithWeather]

class MultiRouteResponseSchema(BaseModel):
    routes: List[SingleRouteOption]