import logging
import asyncio
from app.database import db
from app.services.imd_scraper import scrape_imd_weather_alerts

logger = logging.getLogger(__name__)

async def sync_imd_weather_to_db():
    try:
        loop = asyncio.get_running_loop()
        alerts = await loop.run_in_executor(None, scrape_imd_weather_alerts)

        if not alerts:
            logger.info("[IMD SYNC] No new severe weather alerts returned.")
            return

        for alert in alerts:
            weather_doc = {
                "title": alert["title"],
                "description": alert["description"],
                "source": alert["source"],
                "category": "weather_hazard",
                "created_at": alert["timestamp"],
                "is_active": True,
                "bounding_box": {
                    "min_lat": 26.50,
                    "max_lat": 27.20,
                    "min_lon": 88.10,
                    "max_lon": 88.80
                }
            }
            
            # Asynchronous upsert using AstraRoute's db instance
            await db.disaster_reports.update_one(
                {"title": alert["title"]},
                {"$set": weather_doc},
                upsert=True
            )
        logger.info(f"[IMD SYNC] Successfully synced {len(alerts)} weather alerts to MongoDB.")
    except Exception as e:
        logger.error(f"[IMD SYNC ERROR] {str(e)}")