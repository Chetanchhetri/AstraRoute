from pydantic import BaseModel
from typing import List

class Coordinate(BaseModel):
    latitude: float
    longitude: float

class NavigationRequest(BaseModel):
    start: Coordinate
    destination: Coordinate
    avoid_risk: bool = True

class RouteResponse(BaseModel):
    path: List[Coordinate]
    distance_km: float
    risk_score: float
