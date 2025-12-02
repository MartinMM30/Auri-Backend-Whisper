import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["auri_db"]

# Colecciones
users = db["users"]                   # perfil del usuario
facts = db["facts"]                   # hechos importantes
dialog_recent = db["dialog_recent"]   # memoria corta (últimos 20 mensajes)
memory_vectors = db["memory_vectors"] # memoria semántica (embeddings)
