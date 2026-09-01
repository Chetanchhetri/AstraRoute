from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class WaypointModel(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = "Stop"

class RouteHistoryDocument(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_email: str
    start: WaypointModel
    end: WaypointModel
    stops: List[WaypointModel] = []
    total_distance_meters: float
    total_duration_seconds: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True