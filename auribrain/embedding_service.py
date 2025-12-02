# auribrain/embedding_service.py

import datetime
from openai import OpenAI
from auribrain.memory_db import memory_vectors

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI()

    # ---------------------------------------------
    # Crear embedding y guardarlo
    # ---------------------------------------------
    def save_memory(self, user_id: str, text: str):
        emb = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )

        vec = emb.data[0].embedding

        memory_vectors.insert_one({
            "user_id": user_id,
            "text": text,
            "vector": vec,
            "ts": datetime.datetime.utcnow()
        })

    # ---------------------------------------------
    # Buscar memorias relacionadas
    # ---------------------------------------------
    def search(self, user_id: str, query: str, limit: int = 5):
        emb = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        q_vec = emb.data[0].embedding

        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$vectorSearch": {
                    "queryVector": q_vec,
                    "path": "vector",
                    "limit": limit
                }
            }
        ]

        results = memory_vectors.aggregate(pipeline)

        return [r["text"] for r in results]
