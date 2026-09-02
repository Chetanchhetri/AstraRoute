import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, route, admin, trip, disaster

# Initialize the async task scheduler for background scraping
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Establish MongoDB connection on startup
    await connect_to_mongo()
    
    # 2. Schedule automated Scrapling news scraper to run every 1 hour
    scheduler.add_job(
        disaster.scrape_and_ingest_india_climate_news, 
        'interval', 
        hours=1, 
        id='hourly_climate_scraper'
    )
    scheduler.start()

    yield

    # 3. Clean up scheduler and DB connections on shutdown
    scheduler.shutdown()
    await close_mongo_connection()
    
app = FastAPI(
    title="OSRM Route Optimization API",
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

# Redirect root path to the index UI
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/app/index.html")

# Register distinct modular routers (duplicates removed)
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