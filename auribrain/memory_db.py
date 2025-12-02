import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["auri_db"]

# Colecciones correctas
users = db["users"]
facts = db["facts"]
dialog_recent = db["dialog_recent"]
memory_vectors = db["memory_vectors"]
