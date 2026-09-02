import random
import math
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from app.database import db
from app.config import settings
from app.schemas.auth import RegisterInitiateSchema, VerifyOTPSchema
from app.utils.security import hash_password
from app.services.email_service import send_otp_email_sync

router = APIRouter(tags=["Authentication & Routes"])

# ------------------------------------------------------------------
# Request & Response Schemas
# ------------------------------------------------------------------

class LocationSchema(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None

class AvoidBoxSchema(BaseModel):
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

class OptimizeRouteRequest(BaseModel):
    start: LocationSchema
    end: LocationSchema
    waypoints: Optional[List[LocationSchema]] = []
    avoid_boxes: Optional[List[AvoidBoxSchema]] = []
    round_trip: Optional[bool] = False


# ------------------------------------------------------------------
# Spatial Helpers: Polyline Intersection & Perimeter Detour Generator
# ------------------------------------------------------------------

def is_point_in_box(lat: float, lon: float, box: AvoidBoxSchema) -> bool:
    """Checks if a single point lands inside or near a blocked box boundary."""
    buffer = 0.0005  # Geographic threshold (~50m)
    return (box.min_lat - buffer <= lat <= box.max_lat + buffer) and \
           (box.min_lon - buffer <= lon <= box.max_lon + buffer)

def polyline_intersects_any_box(coordinates: List[List[float]], avoid_boxes: List[AvoidBoxSchema]) -> bool:
    """Evaluates if any [lon, lat] coordinate in the OSRM geometry hits a blocked region."""
    if not avoid_boxes:
        return False
    for lon, lat in coordinates:
        for box in avoid_boxes:
            if is_point_in_box(lat, lon, box):
                return True
    return False

def generate_perimeter_bypass_candidates(start: LocationSchema, end: LocationSchema, avoid_boxes: List[AvoidBoxSchema]) -> List[dict]:
    """Generates dynamic perimeter detour waypoints across 4 directions (N, S, E, W) around blocked boxes."""
    candidates = []
    for box in avoid_boxes:
        lat_center = (box.min_lat + box.max_lat) / 2.0
        lon_center = (box.min_lon + box.max_lon) / 2.0
        
        for offset_factor in [0.015, 0.03, 0.06]:
            d_lat = ((box.max_lat - box.min_lat) / 2.0) + offset_factor
            d_lon = ((box.max_lon - box.min_lon) / 2.0) + offset_factor

            potential_pts = [
                {"latitude": lat_center, "longitude": box.min_lon - d_lon},  # West
                {"latitude": lat_center, "longitude": box.max_lon + d_lon},  # East
                {"latitude": box.max_lat + d_lat, "longitude": lon_center},  # North
                {"latitude": box.min_lat - d_lat, "longitude": lon_center},  # South
            ]
            
            for pt in potential_pts:
                if not any(is_point_in_box(pt["latitude"], pt["longitude"], b) for b in avoid_boxes):
                    candidates.append(pt)

    def detour_cost(pt):
        d1 = math.hypot(pt["latitude"] - start.latitude, pt["longitude"] - start.longitude)
        d2 = math.hypot(end.latitude - pt["latitude"], end.longitude - pt["longitude"])
        return d1 + d2

    return sorted(candidates, key=detour_cost)


# ------------------------------------------------------------------
# Authentication Routes (/api/v1/auth)
# ------------------------------------------------------------------

@router.post("/api/v1/auth/register/initiate")
async def initiate_registration(req: RegisterInitiateSchema, background_tasks: BackgroundTasks):
    try:
        users_col = db["users"]
        pending_users_col = db["pending_users"]

        existing_user = await users_col.find_one({"email": req.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="A user with this email address already exists."
            )

        otp_code = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        pending_user_data = {
            "email": req.email,
            "password_hash": hash_password(req.password),
            "name": req.name,
            "mobile_number": req.mobile_number,
            "is_admin": getattr(req, "is_admin", False),
            "otp": otp_code,
            "expires_at": expires_at,
            "updated_at": datetime.utcnow()
        }

        await pending_users_col.update_one(
            {"email": req.email},
            {"$set": pending_user_data},
            upsert=True
        )

        background_tasks.add_task(send_otp_email_sync, req.email, otp_code)

        return {
            "status": "success",
            "message": f"Verification OTP sent to {req.email}. Please verify within 10 minutes."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration initiation failed: {str(e)}"
        )


@router.post("/api/v1/auth/register/verify")
async def verify_registration(req: VerifyOTPSchema):
    try:
        users_col = db["users"]
        pending_users_col = db["pending_users"]

        pending = await pending_users_col.find_one({"email": req.email})
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No pending registration request found for this email."
            )

        if datetime.utcnow() > pending["expires_at"]:
            await pending_users_col.delete_one({"email": req.email})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="OTP code has expired. Please initiate registration again."
            )

        if pending["otp"] != req.otp.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid OTP code entered."
            )

        final_user_doc = {
            "email": pending["email"],
            "password_hash": pending["password_hash"],
            "name": pending["name"],
            "mobile_number": pending["mobile_number"],
            "is_admin": pending.get("is_admin", False),
            "created_at": datetime.utcnow()
        }

        await users_col.insert_one(final_user_doc)
        await pending_users_col.delete_one({"email": req.email})

        return {
            "status": "success",
            "message": "Account successfully verified and created! You can now log in."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )


# ------------------------------------------------------------------
# Route Optimization Endpoint (/api/v1/route/optimize & /api/v1/routes/optimize)
# ------------------------------------------------------------------

@router.post("/api/v1/route/optimize")
@router.post("/api/v1/routes/optimize")
async def optimize_route(req: OptimizeRouteRequest):
    try:
        async def fetch_osrm_routes(points: List[dict]):
            coord_pairs = [f"{pt['longitude']},{pt['latitude']}" for pt in points]
            coordinates_str = ";".join(coord_pairs)
            osrm_url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{coordinates_str}"
            params = {
                "overview": "full",
                "geometries": "geojson",
                "alternatives": "true"
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.get(osrm_url, params=params, timeout=10.0)
                if res.status_code == 200:
                    return res.json().get("routes", [])
            return []

        # 1. Primary Direct Route Calculation
        base_points = [{"latitude": req.start.latitude, "longitude": req.start.longitude}]
        for wp in req.waypoints:
            base_points.append({"latitude": wp.latitude, "longitude": wp.longitude})
        base_points.append({"latitude": req.end.latitude, "longitude": req.end.longitude})

        routes = await fetch_osrm_routes(base_points)
        valid_routes = []

        for idx, route in enumerate(routes):
            coords = route.get("geometry", {}).get("coordinates", [])
            if not polyline_intersects_any_box(coords, req.avoid_boxes):
                valid_routes.append({
                    "title": "Optimal Clear Route" if not req.avoid_boxes else "Bypass Route",
                    "total_distance_meters": route.get("distance"),
                    "total_duration_seconds": route.get("duration"),
                    "geometry_geojson": route.get("geometry")
                })

        # 2. Dynamic Detour Bypass Engine
        if req.avoid_boxes and not valid_routes:
            detour_candidates = generate_perimeter_bypass_candidates(req.start, req.end, req.avoid_boxes)

            for candidate in detour_candidates:
                detour_points = [base_points[0], candidate, base_points[-1]]
                detour_routes = await fetch_osrm_routes(detour_points)

                for d_route in detour_routes:
                    d_coords = d_route.get("geometry", {}).get("coordinates", [])
                    if not polyline_intersects_any_box(d_coords, req.avoid_boxes):
                        valid_routes.append({
                            "title": "Detour Route (Avoiding Blocked Region)",
                            "total_distance_meters": d_route.get("distance"),
                            "total_duration_seconds": d_route.get("duration"),
                            "geometry_geojson": d_route.get("geometry")
                        })
                        break
                
                if valid_routes:
                    break

        if not valid_routes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No viable bypass route found around the specified blocked regions."
            )

        return {
            "status": "success",
            "message": "Route calculated successfully",
            "routes": valid_routes,
            "osrm_endpoint": settings.OSRM_BASE_URL
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize route: {str(e)}"
        )