# auribrain/memory_orchestrator.py

import datetime
from auribrain.memory_db import users, facts, dialog_recent
from auribrain.embedding_service import EmbeddingService

class MemoryOrchestrator:
    def __init__(self):
        self.embedder = EmbeddingService()

    # ==================================================
    # DIÁLOGO RECIENTE (para el prompt)
    # ==================================================
    def add_dialog(self, user_id: str, role: str, text: str):
        dialog_recent.insert_one({
            "user_id": user_id,
            "role": role,
            "text": text,
            "ts": datetime.datetime.utcnow()
        })

        # limpiar historial a máximo 40 mensajes
        count = dialog_recent.count_documents({"user_id": user_id})
        if count > 40:
            excess = count - 40
            dialog_recent.delete_many({"user_id": user_id}, limit=excess)

    def get_recent_dialog(self, user_id: str, n: int = 10):
        cur = dialog_recent.find({"user_id": user_id}).sort("ts", -1).limit(n * 2)
        lines = []
        for m in reversed(list(cur)):
            prefix = "Usuario" if m["role"] == "user" else "Auri"
            lines.append(f"{prefix}: {m['text']}")
        return "\n".join(lines)

    # ==================================================
    # FACTOS DURADEROS
    # ==================================================
    def add_fact(self, user_id: str, fact: str):
        facts.insert_one({
            "user_id": user_id,
            "fact": fact,
            "ts": datetime.datetime.utcnow()
        })

    def get_facts(self, user_id: str):
        cur = facts.find({"user_id": user_id})
        return [f["fact"] for f in cur]

    # ==================================================
    # SEMANTIC MEMORY (EMBEDDINGS)
    # ==================================================
    def add_semantic(self, user_id: str, text: str):
        self.embedder.save_memory(user_id, text)

    def search_semantic(self, user_id: str, query: str):
        return self.embedder.search(user_id, query)

    # ==================================================
    # PERFIL DEL USUARIO
    # ==================================================
    def get_user_profile(self, user_id: str):
        doc = users.find_one({"_id": user_id})
        return doc or {}

    def update_user_profile(self, user_id: str, data: dict):
        users.update_one({"_id": user_id}, {"$set": data}, upsert=True)
