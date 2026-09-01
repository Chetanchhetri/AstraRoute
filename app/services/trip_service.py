import httpx
import math
from typing import List, Optional
from fastapi import HTTPException
from app.config import settings
from app.schemas.trip import DetailedTripRequest, DetailedTripResponse, DetailedPOI, TripItinerarySegment
from app.schemas.route import RouteRequestSchema
from app.services.osrm_service import OSRMService

class TripService:
    # Expanded database of POIs across major Indian highway transit corridors
    MASTER_POIS = [
        # --- Heritage & Spiritual ---
        DetailedPOI(name="Ayodhya Ram Mandir", category="attraction", subcategory="spiritual", latitude=26.7922, longitude=82.1998, description="Historic spiritual center in Ayodhya.", detour_distance_km=0.0, estimated_visit_minutes=120),
        DetailedPOI(name="Varanasi Dashashwamedh Ghat", category="attraction", subcategory="spiritual", latitude=25.3076, longitude=83.0101, description="Famous Ganga Ghat in Varanasi.", detour_distance_km=0.0, estimated_visit_minutes=90),
        DetailedPOI(name="Taj Mahal", category="attraction", subcategory="heritage", latitude=27.1751, longitude=78.0421, description="UNESCO Heritage monument in Agra.", detour_distance_km=0.0, estimated_visit_minutes=150),
        DetailedPOI(name="Qutub Minar", category="attraction", subcategory="heritage", latitude=28.5245, longitude=77.1855, description="Historical monument in New Delhi.", detour_distance_km=0.0, estimated_visit_minutes=60),
        DetailedPOI(name="Konark Sun Temple", category="attraction", subcategory="heritage", latitude=19.8876, longitude=86.0945, description="13th-century Sun Temple near Odisha coast.", detour_distance_km=0.0, estimated_visit_minutes=90),
        DetailedPOI(name="Tirupati Balaji Temple", category="attraction", subcategory="spiritual", latitude=13.6833, longitude=79.3472, description="Famous hill shrine in Andhra Pradesh.", detour_distance_km=0.0, estimated_visit_minutes=180),

        # --- Stays & Hotels ---
        DetailedPOI(name="Gorakhpur Heritage Hotel", category="hotel", subcategory="medium", latitude=26.7606, longitude=83.3732, description="Comfortable highway stay over point.", detour_distance_km=0.0, estimated_visit_minutes=480),
        DetailedPOI(name="Lucknow Express Inn", category="hotel", subcategory="budget", latitude=26.8467, longitude=80.9462, description="Midway hotel near Lucknow expressway.", detour_distance_km=0.0, estimated_visit_minutes=480),
        DetailedPOI(name="Agra Palace Resort", category="hotel", subcategory="luxury", latitude=27.1800, longitude=78.0200, description="Luxury stay near Taj Expressway.", detour_distance_km=0.0, estimated_visit_minutes=480),
        DetailedPOI(name="Bhubaneswar Grand Hotel", category="hotel", subcategory="medium", latitude=20.2961, longitude=85.8245, description="Transit stay near Odisha Highway.", detour_distance_km=0.0, estimated_visit_minutes=480),
        DetailedPOI(name="Vijayawada Riverfront Resort", category="hotel", subcategory="luxury", latitude=16.5062, longitude=80.6480, description="Resort near Krishna river express line.", detour_distance_km=0.0, estimated_visit_minutes=480),

        # --- Fuel & EV Plazas ---
        DetailedPOI(name="Indian Oil Swagat Station (Purnea)", category="petrol_pump", subcategory="fuel", latitude=25.7771, longitude=87.4753, description="24/7 Fuel & Food Plaza.", detour_distance_km=0.0, estimated_visit_minutes=20),
        DetailedPOI(name="BPCL Fuel & EV Oasis (Muzaffarpur)", category="ev_charger", subcategory="ev", latitude=26.1209, longitude=85.3647, description="High-speed DC Fast EV Charger & Diesel Depot.", detour_distance_km=0.0, estimated_visit_minutes=45),
        DetailedPOI(name="HPCL Express Fuel (Kanpur)", category="petrol_pump", subcategory="fuel", latitude=26.4499, longitude=80.3319, description="Major refuel stop with clean amenities.", detour_distance_km=0.0, estimated_visit_minutes=20),
        DetailedPOI(name="Kharagpur Tata Power EV Hub", category="ev_charger", subcategory="ev", latitude=22.3460, longitude=87.2320, description="Dual 60kW EV Fast Chargers on NH16.", detour_distance_km=0.0, estimated_visit_minutes=40),
        DetailedPOI(name="HPCL Swagat Station (Visakhapatnam)", category="petrol_pump", subcategory="fuel", latitude=17.6868, longitude=83.2185, description="24/7 highway fuel & refreshment plaza.", detour_distance_km=0.0, estimated_visit_minutes=25),

        # --- Restaurants ---
        DetailedPOI(name="Highway Dhaba (Darbhanga)", category="restaurant", subcategory="food", latitude=26.1542, longitude=85.8918, description="Authentic regional highway meals.", detour_distance_km=0.0, estimated_visit_minutes=45),
        DetailedPOI(name="Lucknow Awadhi Express Dining", category="restaurant", subcategory="food", latitude=26.8500, longitude=80.9500, description="Famous local cuisine stop.", detour_distance_km=0.0, estimated_visit_minutes=60),
        DetailedPOI(name="Vizag Coastal Food Court", category="restaurant", subcategory="food", latitude=17.7200, longitude=83.3000, description="Fresh seafood dining along NH16.", detour_distance_km=0.0, estimated_visit_minutes=50)
    ]

    @staticmethod
    def calculate_min_distance_to_route(poi_lat: float, poi_lon: float, route_coords: List[List[float]]) -> float:
        """Calculates minimum distance in km from a POI to any segment along the GeoJSON route."""
        min_dist = float('inf')
        for point in route_coords[::4]:  # Sub-sample coordinates to boost execution speed
            r_lon, r_lat = point[0], point[1]
            dist_km = math.hypot(poi_lat - r_lat, poi_lon - r_lon) * 111.0  # 1 degree ~ 111 km
            if dist_km < min_dist:
                min_dist = dist_km
        return round(min_dist, 1)

    @classmethod
    async def plan_trip(cls, req: DetailedTripRequest) -> DetailedTripResponse:
        coords_str = f"{req.start.longitude},{req.start.latitude};{req.end.longitude},{req.end.latitude}"
        route_url = f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{coords_str}"
        
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get(route_url, params={"alternatives": "true", "geometries": "geojson", "overview": "full"})
            if res.status_code != 200 or not res.json().get("routes"):
                raise HTTPException(status_code=400, detail="Could not calculate route path.")
                
            res_data = res.json()
            selected_route = None
            
            # 1. Filter out routes that cross blocked regions
            for candidate in res_data["routes"]:
                geom_coords = candidate.get("geometry", {}).get("coordinates", [])
                if not (req.avoid_boxes and OSRMService.is_route_blocked(geom_coords, req.avoid_boxes)):
                    selected_route = candidate
                    break

            # 2. Trigger automated detour fallback if all direct routes hit a blocked region
            if not selected_route:
                fallback_req = RouteRequestSchema(
                    start=req.start,
                    end=req.end,
                    stops=req.stops,
                    avoid_boxes=req.avoid_boxes,
                    round_trip=False
                )
                
                detour_res = await OSRMService.get_optimized_routes(fallback_req)
                selected_route = {
                    "distance": detour_res.routes[0].total_distance_meters,
                    "duration": detour_res.routes[0].total_duration_seconds,
                    "geometry": detour_res.routes[0].geometry_geojson
                }

            route_geometry = selected_route["geometry"]
            route_coords = route_geometry.get("coordinates", [])
            dist_km = round(selected_route["distance"] / 1000, 2)
            dur_hrs = round(selected_route["duration"] / 3600, 1)

            # 3. Match POIs strictly by spatial proximity and user preferences
            matched_pois = []
            pref = req.preferences

            for poi in cls.MASTER_POIS:
                # Category toggles
                if poi.category == "petrol_pump" and not pref.include_petrol_pumps: continue
                if poi.category == "ev_charger" and not pref.include_ev_chargers: continue
                if poi.category == "hotel" and not pref.include_hotels: continue
                if poi.category == "restaurant" and not pref.include_restaurants: continue
                if poi.category == "attraction" and not pref.include_attractions: continue

                # Specific interest filter for attractions
                if pref.interests and poi.category == "attraction":
                    if poi.subcategory not in pref.interests:
                        continue

                # Spatial distance check against route geometry
                detour = cls.calculate_min_distance_to_route(poi.latitude, poi.longitude, route_coords)
                if detour <= pref.max_detour_km:
                    poi_copy = poi.model_copy()
                    poi_copy.detour_distance_km = detour
                    matched_pois.append(poi_copy)

            # 4. Estimate suggested trip span
            daily_hours = 6.0 if pref.trip_pace == "scenic_detours" else (10.0 if pref.trip_pace == "express" else 8.0)
            suggested_days = max(1, math.ceil(dur_hrs / daily_hours))

            # 5. Build day-by-day itinerary segments
            itinerary = []
            pois_per_day = max(1, math.ceil(len(matched_pois) / suggested_days)) if matched_pois else 0
            
            for d in range(1, suggested_days + 1):
                day_stops = matched_pois[(d - 1) * pois_per_day : d * pois_per_day]
                itinerary.append(TripItinerarySegment(
                    day=d,
                    title=f"Day {d}: Highway Transit & Scheduled Stops",
                    suggested_stops=day_stops
                ))

            start_label = req.start.name if req.start.name and req.start.name != "Stop" else "Start"
            end_label = req.end.name if req.end.name and req.end.name != "Stop" else "Destination"

            return DetailedTripResponse(
                title=f"Custom Trip: {start_label} to {end_label}",
                travel_mode=pref.travel_mode,
                total_distance_km=dist_km,
                total_duration_hours=dur_hrs,
                suggested_days=suggested_days,
                pois=matched_pois,
                itinerary=itinerary,
                route_geometry=route_geometry
            )