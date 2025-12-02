import datetime
from auribrain.memory_db import users, facts, dialog_recent
from auribrain.embedding_service import EmbeddingService
from auribrain.memory_router import router
from auribrain.memory_db import memory_vectors


class MemoryOrchestrator:

    def __init__(self):
        self.embedder = EmbeddingService()

    # ==================================================
    # DIÁLOGO RECIENTE
    # ==================================================
    def add_dialog(self, user_id: str, role: str, text: str):
        dialog_recent.insert_one({
            "user_id": user_id,
            "role": role,
            "text": text,
            "ts": datetime.datetime.utcnow()
        })

        # limpiar historial a máximo 40 mensajes
        cur = dialog_recent.find({"user_id": user_id}).sort("ts", -1)
        msgs = list(cur)

        if len(msgs) > 40:
            to_delete = msgs[40:]  # todo lo que sobra
            ids = [m["_id"] for m in to_delete]
            dialog_recent.delete_many({"_id": {"$in": ids}})

    def get_recent_dialog(self, user_id, n=10):
        cur = dialog_recent.find({"user_id": user_id}).sort("ts", -1).limit(n * 2)
        lines = []
        for m in reversed(list(cur)):
            prefix = "Usuario" if m["role"] == "user" else "Auri"
            lines.append(f"{prefix}: {m['text']}")
        return "\n".join(lines)

    # ==================================================
    # FACTOS DURADEROS
    # ==================================================
    def add_fact(self, user_id, fact_text):
        facts.insert_one({
            "user_id": user_id,
            "fact": fact_text,
            "ts": datetime.datetime.utcnow()
        })

    def get_facts(self, user_id):
        return [f["fact"] for f in facts.find({"user_id": user_id})]

    # ==================================================
    # MEMORIA SEMÁNTICA (EMBEDDINGS)
    # ==================================================
    def add_semantic(self, user_id: str, text: str):
        """Guarda recuerdos relevantes usando prioridad."""
        text_low = text.lower()

        IMPORTANT = [
            "me gusta", "mi comida favorita", "odio", "mi novia", "mi pareja",
            "mi mamá", "mi papá", "trabajo", "estoy estudiando",
            "soy de", "vivo en", "quiero lograr", "mi sueño", "mis metas",
            "mi color favorito", "mi cantante favorito"
        ]

        # Solo guardar si es importante
        if any(k in text_low for k in IMPORTANT):
            self.embedder.add(user_id, text)



    def search_semantic(self, user_id: str, query: str):
        return self.embedder.search(user_id, query)

    # ==================================================
    # PERFIL DEL USUARIO
    # ==================================================
    def get_user_profile(self, user_id: str):
        return users.find_one({"_id": user_id}) or {}

    def update_user_profile(self, user_id: str, data: dict):
        users.update_one({"_id": user_id}, {"$set": data}, upsert=True)
