from openai import OpenAI
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")
mongo = MongoClient(MONGO_URI)
db = mongo["auri_db"]
memory_vectors = db["memory_vectors"]

client = OpenAI()

class EmbeddingService:

    def embed(self, text: str):
        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return [float(x) for x in res.data[0].embedding]

    def add(self, user_id: str, text: str):
        vec = self.embed(text)

        memory_vectors.insert_one({
            "user_id": user_id,
            "text": text,
            "embedding": vec
        })

    def search(self, user_id: str, query: str):
        qvec = self.embed(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "memory_vectors_index",
                    "path": "embedding",
                    "queryVector": qvec,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": {"user_id": user_id}
                }
            },
            {
                "$project": {"text": 1, "_id": 0}
            }
        ]

        results = memory_vectors.aggregate(pipeline)
        return [r.get("text", "") for r in results]
