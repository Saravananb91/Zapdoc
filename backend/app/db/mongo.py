from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "OCR_db")

client = AsyncIOMotorClient(MONGO_URL)
db = client[MONGO_DB]

requests_col = db["test_case"]
documents_col = db["test_case_doc"]
