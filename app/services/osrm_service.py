from typing import Optional, List
import httpx
import math
from fastapi import HTTPException, status
from app.config import settings
from app.schemas.route import (
    RouteRequestSchema, 
    MultiRouteResponseSchema, 
    SingleRouteOption, 
    WaypointWithWeather, 
    WeatherInfo,
    BoundingBox
)

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers", 95: "Thunderstorm"
}

class OSRMService:
    @staticmethod
    def is_route_blocked(geometry_coordinates: List[List[float]], avoid_boxes: List[BoundingBox]) -> bool:
        """Validates if any [lon, lat] coordinate in the geometry intersects ANY blocked box."""
        for point in geometry_coordinates:
            if len(point) < 2:
                continue
            lon, lat = point[0], point[1]
            for box in avoid_boxes:
                if (box.min_lat - 0.0005) <= lat <= (box.max_lat + 0.0005) and \
                   (box.min_lon - 0.0005) <= lon <= (box.max_lon + 0.0005):
                    return True
        return False

    @staticmethod
    def generate_multi_box_detours(start: tuple, end: tuple, avoid_boxes: List[BoundingBox]) -> List[tuple]:
        """Generates progressive perimeter bypass waypoints around ALL blocked boxes."""
        candidates = []
        
        for box in avoid_boxes:
            lat_center = (box.min_lat + box.max_lat) / 2.0
            lon_center = (box.min_lon + box.max_lon) / 2.0
            
            for offset in [0.02, 0.05, 0.09, 0.15]:
                d_lat = ((box.max_lat - box.min_lat) / 2.0) + offset
                d_lon = ((box.max_lon - box.min_lon) / 2.0) + offset

                candidates.extend([
                    (lat_center + d_lat, lon_center + d_lon),
                    (lat_center + d_lat, lon_center - d_lon),
                    (lat_center - d_lat, lon_center + d_lon),
                    (lat_center - d_lat, lon_center - d_lon),
                    (lat_center + d_lat, lon_center),
                    (lat_center - d_lat, lon_center),
                    (lat_center, lon_center + d_lon),
                    (lat_center, lon_center - d_lon)
                ])

        # Filter out candidate points that fall inside ANY of the blocked boxes
        valid_candidates = []
        for lat, lon in candidates:
            inside_any = False
            for box in avoid_boxes:
                if box.min_lat <= lat <= box.max_lat and box.min_lon <= lon <= box.max_lon:
                    inside_any = True
                    break
            if not inside_any:
                valid_candidates.append((lat, lon))

        # Sort candidate detour points by minimum total distance
        def detour_cost(pt):
            return math.hypot(pt[0] - start[0], pt[1] - start[1]) + math.hypot(end[0] - pt[0], end[1] - pt[1])

        return sorted(valid_candidates, key=detour_cost)

    @staticmethod
    async def fetch_weather_for_point(client: httpx.AsyncClient, lat: float, lon: float) -> Optional[WeatherInfo]:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability"
            res = await client.get(url, timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                cw = data.get("current_weather", {})
                hourly_rain = data.get("hourly", {}).get("precipitation_probability", [0])
                rain_prob = int(hourly_rain[0]) if hourly_rain else 0

                return WeatherInfo(
                    temperature_celsius=float(cw.get("temperature", 0.0)),
                    weather_condition=WEATHER_CODES.get(cw.get("weathercode", 0), "Clear"),
                    wind_speed_kmh=float(cw.get("windspeed", 0.0)),
                    precipitation_probability_percent=rain_prob
                )
        except Exception:
            pass
        return None

    @classmethod
    async def get_optimized_routes(cls, route_req: RouteRequestSchema) -> MultiRouteResponseSchema:
        all_points = [route_req.start] + route_req.stops + [route_req.end]
        coords_str = ";".join([f"{pt.longitude},{pt.latitude}" for pt in all_points])
        
        valid_options = []
        
        async with httpx.AsyncClient(timeout=25.0) as client:
            # 1. Primary Direct Route Query
            route_url = f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{coords_str}"
            params = {"alternatives": "3", "geometries": "geojson", "overview": "full"}
            
            response = await client.get(route_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    for route_data in data["routes"]:
                        coords = route_data.get("geometry", {}).get("coordinates", [])
                        
                        if not (route_req.avoid_boxes and cls.is_route_blocked(coords, route_req.avoid_boxes)):
                            wps_with_weather = []
                            for pt in all_points:
                                w = await cls.fetch_weather_for_point(client, pt.latitude, pt.longitude)
                                wps_with_weather.append(WaypointWithWeather(
                                    latitude=pt.latitude, longitude=pt.longitude, name=pt.name, weather=w
                                ))

                            valid_options.append({
                                "distance": float(route_data.get("distance", 0)),
                                "duration": float(route_data.get("duration", 0)),
                                "geometry": route_data.get("geometry", {}),
                                "waypoints": wps_with_weather
                            })

            # 2. Multi-Box Bypass Engine (Evaluates ALL blocked boxes simultaneously)
            if not valid_options and route_req.avoid_boxes:
                start_tuple = (route_req.start.latitude, route_req.start.longitude)
                end_tuple = (route_req.end.latitude, route_req.end.longitude)
                
                detour_candidates = cls.generate_multi_box_detours(start_tuple, end_tuple, route_req.avoid_boxes)

                for detour_lat, detour_lon in detour_candidates:
                    detour_pts = [route_req.start] + route_req.stops + [
                        WaypointWithWeather(latitude=detour_lat, longitude=detour_lon, name="Bypass Node")
                    ] + [route_req.end]
                    
                    detour_str = ";".join([f"{pt.longitude},{pt.latitude}" for pt in detour_pts])
                    detour_url = f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{detour_str}"
                    
                    detour_res = await client.get(detour_url, params={
                        "geometries": "geojson", 
                        "overview": "full", 
                        "radiuses": ";".join(["unlimited" for _ in detour_pts])
                    })

                    if detour_res.status_code == 200:
                        detour_data = detour_res.json()
                        if detour_data.get("code") == "Ok" and detour_data.get("routes"):
                            d_route = detour_data["routes"][0]
                            d_coords = d_route.get("geometry", {}).get("coordinates", [])
                            
                            # Verify route completely clears ALL blocked regions
                            if not cls.is_route_blocked(d_coords, route_req.avoid_boxes):
                                wps_with_weather = []
                                for pt in [route_req.start, route_req.end]:
                                    w = await cls.fetch_weather_for_point(client, pt.latitude, pt.longitude)
                                    wps_with_weather.append(WaypointWithWeather(
                                        latitude=pt.latitude, longitude=pt.longitude, name=pt.name, weather=w
                                    ))

                                valid_options.append({
                                    "distance": float(d_route.get("distance", 0)),
                                    "duration": float(d_route.get("duration", 0)),
                                    "geometry": d_route.get("geometry", {}),
                                    "waypoints": wps_with_weather
                                })

                                if len(valid_options) >= 2:
                                    break

        if not valid_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No viable bypass route found around the blocked region."
            )

        # Sort all valid routes by total distance
        valid_options.sort(key=lambda x: x["distance"])

        final_routes = []
        for idx, opt in enumerate(valid_options[:3]):
            title = "Route 1 (Optimal Clear Path)" if idx == 0 else f"Route {idx+1} (Alternative Path)"
            final_routes.append(SingleRouteOption(
                title=title,
                total_distance_meters=opt["distance"],
                total_duration_seconds=opt["duration"],
                geometry_geojson=opt["geometry"],
                ordered_waypoints=opt["waypoints"]
            ))

        return MultiRouteResponseSchema(routes=final_routes)