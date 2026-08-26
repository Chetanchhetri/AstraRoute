from fastapi import APIRouter
from app.schemas.navigation import NavigationRequest, RouteResponse
from app.services.router_service import optimize_route

router = APIRouter()

@router.post("/route", response_model=RouteResponse)
def calculate_route(request: NavigationRequest):
    return optimize_route(request)
