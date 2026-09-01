from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.trip import DetailedTripRequest, DetailedTripResponse
from app.services.trip_service import TripService
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/trip", tags=["Trip Planner"])

@router.post("/plan", response_model=DetailedTripResponse)
async def plan_detailed_trip(
    req: DetailedTripRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generates long-distance route geometries, spatial POI matching, and day-by-day itineraries."""
    try:
        return await TripService.plan_trip(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trip plan: {str(e)}"
        )