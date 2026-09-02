from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class Database:
    client: AsyncIOMotorClient = None

    @property
    def get_db(self):
        """Returns the active MongoDB database instance pulling name from .env settings."""
        if self.client is None:
            raise RuntimeError("Database client is not initialized. Ensure connect_to_mongo() has been executed.")
        return self.client[settings.MONGO_DB_NAME]

    def __getattr__(self, name: str):
        """Allows direct attribute access for collections (e.g., db.users)."""
        return getattr(self.get_db, name)

    def __getitem__(self, name: str):
        """Allows direct bracket notation for collections (e.g., db["users"])."""
        return self.get_db[name]

db = Database()

async def connect_to_mongo():
    # Connect using MONGO_URI from .env
    db.client = AsyncIOMotorClient(settings.MONGO_URI)
    print(f"Connected to MongoDB database: {settings.MONGO_DB_NAME}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")

def get_database():
    return db.get_db