from pymongo import MongoClient
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DataBase:
    client: MongoClient = None
    database = None

database = DataBase()

async def connect_to_mongo():
    try:
        database.client = MongoClient(settings.MONGODB_URL)
        database.database = database.client[settings.DATABASE_NAME]
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")


def get_database():
    return database.database
