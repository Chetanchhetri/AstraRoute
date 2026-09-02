from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DisasterReportCreateSchema(BaseModel):
    disaster_type: str = Field(..., example="Landslide")
    description: Optional[str] = Field(None, example="Road blocked due to mudslide.")
    latitude: float = Field(..., example=26.7132)
    longitude: float = Field(..., example=88.4323)
    radius_km: float = Field(0.5, description="Affected radius around the point in kilometers")
    duration_hours: int = Field(6, description="How long this alert remains active")

class DisasterReportResponseSchema(BaseModel):
    id: str
    user_email: str
    disaster_type: str
    description: Optional[str]
    latitude: float
    longitude: float
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    created_at: datetime
    expires_at: datetime