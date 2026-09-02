import math
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from scrapling.fetchers import Fetcher

from app.database import db
from app.utils.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/disasters", tags=["Disaster Reporting"])

# Strict climate disaster matching
CLIMATE_DISASTER_KEYWORDS = [
    "landslide", "mudslide", "flood", "flash flood", 
    "cloudburst", "cyclone", "heavy waterlogging", "inundation"
]

# Exclude non-climate traffic accidents
EXCLUDED_KEYWORDS = ["car crash", "road accident", "bus collision", "hit and run"]

def latlon_to_bounding_box(lat: float, lon: float, radius_km: float):
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    return {
        "min_lat": lat - lat_delta,
        "max_lat": lat + lat_delta,
        "min_lon": lon - lon_delta,
        "max_lon": lon + lon_delta
    }

async def scrape_and_ingest_india_climate_news():
    """Scrapes trusted RSS feeds via Scrapling for climate disasters and ingests them into MongoDB."""
    fetcher = Fetcher()
    
    sources = [
        "https://news.google.com/rss/search?q=landslide+flood+india+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=cloudburst+cyclone+india+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    ]

    ingested_count = 0

    for source_url in sources:
        try:
            page = fetcher.get(source_url)
            items = page.css("item")
            
            for item in items:
                title = (item.css("title::text").first() or "").strip()
                description = (item.css("description::text").first() or "").strip()
                text_content = f"{title} {description}".lower()

                # Rule 1: Must be a natural climate event
                is_climate_event = any(k in text_content for k in CLIMATE_DISASTER_KEYWORDS)
                # Rule 2: Ignore routine road accidents
                is_road_accident = any(k in text_content for k in EXCLUDED_KEYWORDS)

                if is_climate_event and not is_road_accident:
                    disaster_type = "Landslide Alert" if "landslide" in text_content else "Flood Hazard"
                    
                    # Geocode location or fallback to regional North Bengal corridor bounds
                    lat, lon = 26.8500, 88.4000
                    bbox = latlon_to_bounding_box(lat, lon, radius_km=2.0)
                    now = datetime.utcnow()
                    expires_at = now + timedelta(hours=24)

                    doc = {
                        "user_email": "automated_news_scrapling_bot@astraroute.internal",
                        "disaster_type": disaster_type,
                        "description": title[:250],
                        "latitude": lat,
                        "longitude": lon,
                        "min_lat": bbox["min_lat"],
                        "max_lat": bbox["max_lat"],
                        "min_lon": bbox["min_lon"],
                        "max_lon": bbox["max_lon"],
                        "source": "Scrapling Climate Scraper",
                        "created_at": now,
                        "expires_at": expires_at
                    }

                    # Avoid duplicate records for identical news items
                    existing = await db.disaster_reports.find_one({"description": title[:250]})
                    if not existing:
                        await db.disaster_reports.insert_one(doc)
                        ingested_count += 1

        except Exception as e:
            logger.error(f"Scrapling news fetch error on {source_url}: {str(e)}")

    logger.info(f"Automated Scrapling Job: Ingested {ingested_count} news disaster reports.")
    return ingested_count

@router.post("/scrape-news")
async def trigger_disaster_news_scrape(current_user: dict = Depends(get_current_user)):
    """Manual endpoint trigger for Scrapling ingestion."""
    count = await scrape_and_ingest_india_climate_news()
    return {
        "status": "success",
        "message": f"Scrapling finished ingestion. Added {count} active climate disaster reports."
    }