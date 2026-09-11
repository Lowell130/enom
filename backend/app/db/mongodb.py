from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

async def get_database():
    return db.client[settings.DATABASE_NAME]

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        minPoolSize=10,
        maxPoolSize=50,
        maxIdleTimeMS=60000
    )
    try:
        await db.client.admin.command('ping')
        print(f"Connected to MongoDB Atlas and pre-warmed connection pool!")
    except Exception as e:
        print(f"MongoDB connection notice: {e}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")
