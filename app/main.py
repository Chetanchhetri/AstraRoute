import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, route, admin, trip, disaster
from app.services.scheduler import sync_imd_weather_to_db

# Initialize the async task scheduler for background jobs
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Establish MongoDB connection on startup
    await connect_to_mongo()
    
    # 2. Schedule news scraper job (every 1 hour)
    scheduler.add_job(
        disaster.scrape_and_ingest_india_climate_news, 
        'interval', 
        hours=1, 
        id='hourly_climate_scraper'
    )

    # 3. Schedule IMD Weather Sync job (every 1 hour)
    scheduler.add_job(
        sync_imd_weather_to_db,
        'interval',
        hours=1,
        id='imd_weather_sync_job',
        replace_existing=True
    )

    # Trigger IMD sync once immediately on startup
    try:
        await sync_imd_weather_to_db()
    except Exception as e:
        print(f"[STARTUP WARN] Initial IMD sync failed: {str(e)}")

    scheduler.start()

    yield

    # 4. Clean up scheduler and DB connections on shutdown
    scheduler.shutdown()
    await close_mongo_connection()

app = FastAPI(
    title="AstraRoute API",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for Leaflet map dashboard
app.mount("/app", StaticFiles(directory="app"), name="app")

# Redirect root path to the public home page
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/app/home.html")

# Register distinct modular routers
app.include_router(auth.router)
app.include_router(route.router)
app.include_router(admin.router)
app.include_router(trip.router)
app.include_router(disaster.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "online", "version": settings.VERSION}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)