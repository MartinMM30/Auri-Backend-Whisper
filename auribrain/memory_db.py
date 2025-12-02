# auribrain/memory_db.py

import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("❌ ERROR: Falta la variable de entorno MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["auri"]

users = db["users"]
facts = db["facts"]
memory_vectors = db["memory_vectors"]
