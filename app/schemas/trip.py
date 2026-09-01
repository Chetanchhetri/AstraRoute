from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.route import Waypoint, BoundingBox

class DetailedTripPreferences(BaseModel):
    travel_mode: str = "driving"
    trip_pace: str = "balanced"
    max_detour_km: float = 25.0
    interests: List[str] = []
    include_petrol_pumps: bool = True
    include_ev_chargers: bool = False
    include_hotels: bool = True
    include_restaurants: bool = True
    include_attractions: bool = True
    budget_level: str = "medium"

class DetailedTripRequest(BaseModel):
    start: Waypoint
    end: Waypoint
    stops: List[Waypoint] = []  # <-- Added missing stops attribute
    preferences: DetailedTripPreferences
    avoid_boxes: List[BoundingBox] = []

class DetailedPOI(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    latitude: float
    longitude: float
    description: str
    detour_distance_km: float = 0.0
    estimated_visit_minutes: int = 30

class TripItinerarySegment(BaseModel):
    day: int
    title: str
    suggested_stops: List[DetailedPOI]

class DetailedTripResponse(BaseModel):
    title: str
    travel_mode: str
    total_distance_km: float
    total_duration_hours: float
    suggested_days: int
    pois: List[DetailedPOI]
    itinerary: List[TripItinerarySegment]
    route_geometry: dict