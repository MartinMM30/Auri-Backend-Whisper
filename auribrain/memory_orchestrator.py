import datetime
from auribrain.memory_db import users, facts, dialog_recent
from auribrain.embedding_service import EmbeddingService

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
        """
        Compatibilidad con funciones antiguas.
        Guarda texto suelto como categoría "other".
        """
        self.add_fact_structured(user_id, {
            "text": fact_text,
            "category": "other",
            "importance": 2,
            "confidence": 0.5
        })


    def get_facts(self, user_id):
        return [
    {
        "text": f.get("text"),
        "category": f.get("category"),
        "importance": f.get("importance"),
        "confidence": f.get("confidence"),
    }
    for f in facts.find({"user_id": user_id, "is_active": True})
]


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
    def add_fact_structured(self, user_id: str, fact: dict):
        """
        Guarda un hecho estructurado:
        - text
        - category
        - importance
        - confidence
        """

        doc = {
            "user_id": user_id,
            "text": fact.get("text"),
            "category": fact.get("category", "other"),
            "importance": fact.get("importance", 3),
            "confidence": fact.get("confidence", 0.8),
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "is_active": True,
        }

        # Evitar duplicados exactos
        exists = facts.find_one({
            "user_id": user_id,
            "text": doc["text"],
            "category": doc["category"],
            "is_active": True
        })

        if exists:
            return  # no guardar duplicados exactos

        facts.insert_one(doc)

