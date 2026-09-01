from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, route, admin, trip  

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
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

# Mount static files so your HTML/CSS/JS files are live on Render/Localhost
app.mount("/app", StaticFiles(directory="app"), name="app")

# Redirect root URL to your main Route Dashboard
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/app/index.html")

app.include_router(auth.router)
app.include_router(route.router)
app.include_router(admin.router)
app.include_router(trip.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "online", "version": settings.VERSION}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)