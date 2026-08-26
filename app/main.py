from fastapi import FastAPI
from app.routes.navigation_routes import router as navigation_router
from app.routes.weather_routes import router as weather_router
import datetime
app = FastAPI(title="SIH26002 Production Platform")

app.include_router(navigation_router, prefix="/api/v1/navigation", tags=["navigation"])
app.include_router(weather_router, prefix="/api/v1/weather", tags=["weather"])

@app.get("/health", tags=["health"])
def root():
    current_time = datetime.datetime.now()
    return {"status": "ok", "service": "SIH26002 Production Platform is running today's date and time.", "current_time": current_time}
