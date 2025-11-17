from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.DATABASE_URL)
print('MongoDB Connected Successfully...')

db = client[settings.MONGO_INITDB_DATABASE]

users = db.users
profiles = db.profiles
pipeline_results = db.pipeline_results
vulnerability_reports = db.vulnerability_reports