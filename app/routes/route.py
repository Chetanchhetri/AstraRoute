from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.route import RouteRequestSchema, MultiRouteResponseSchema
from app.services.osrm_service import OSRMService
from app.utils.security import get_current_user
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routes", tags=["Routing"])

@router.post("/optimize", response_model=MultiRouteResponseSchema)
async def plan_optimized_route(
    route_req: RouteRequestSchema,
    current_user: dict = Depends(get_current_user)
):
    """Calculates multiple route options (Primary + Alternatives) via OSRM and logs to MongoDB."""
    try:
        route_res = await OSRMService.get_optimized_routes(route_req)
        
        # Log to MongoDB
        try:
            db = get_database()
            primary = route_res.routes[0]
            await db.route_history.insert_one({
                "user_email": current_user.get("email"),
                "start": route_req.start.model_dump(),
                "end": route_req.end.model_dump(),
                "stops": [s.model_dump() for s in route_req.stops],
                "total_routes_found": len(route_res.routes),
                "primary_distance_meters": primary.total_distance_meters,
                "primary_duration_seconds": primary.total_duration_seconds
            })
        except Exception as db_exc:
            logger.error(f"Failed to log route history to MongoDB: {db_exc}")

        return route_res

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"Unhandled error in route optimization: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route processing failed: {str(exc)}"
        )