import datetime
from auribrain.memory_db import users, facts, dialog_recent
from auribrain.embedding_service import EmbeddingService


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

        # mantener máximo 40
        cur = dialog_recent.find({"user_id": user_id}).sort("ts", -1)
        msgs = list(cur)
        if len(msgs) > 40:
            to_delete = msgs[40:]
            dialog_recent.delete_many({"_id": {"$in": [m["_id"] for m in to_delete]}})

    def get_recent_dialog(self, user_id, n=10):
        cur = dialog_recent.find({"user_id": user_id}).sort("ts", -1).limit(n * 2)
        lines = []
        for m in reversed(list(cur)):
            prefix = "Usuario" if m["role"] == "user" else "Auri"
            lines.append(f"{prefix}: {m['text']}")
        return "\n".join(lines)

    # ==================================================
    # FACTOS DURADEROS (estructura completa)
    # ==================================================
    def add_fact_structured(self, user_id: str, fact: dict):
        role = self.normalize_role(fact.get("role"))

        """
        Guarda un hecho estructurado con soporte para:
        - text
        - category
        - importance
        - confidence
        - name
        - role  (madre, padre, hermana, abuela…)
        - kind  (perro, gato…)
        - tags
        - type  (family_member, pet, etc.)
        """

        doc = {
            "user_id": user_id,
            "text": fact.get("text"),
            "category": fact.get("category", "other"),
            "importance": fact.get("importance", 3),
            "confidence": fact.get("confidence", 0.8),
            "name": fact.get("name"),
            "role": fact.get("role"),
            "kind": fact.get("kind"),
            "tags": fact.get("tags"),
            "type": fact.get("type"),
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "is_active": True,
        }

        # Duplicado si coincide clave compuesta de los campos estructurados
        exists = facts.find_one({
            "user_id": user_id,
            "text": doc["text"],
            "category": doc["category"],
            "name": doc.get("name"),
            "role": doc.get("role"),
            "kind": doc.get("kind"),
            "is_active": True
        })

        if exists:
            return  # evitar duplicados exactos

        facts.insert_one(doc)

    def get_facts(self, user_id):
        """Devuelve TODOS los facts estructurados usados por AuriMind."""
        result = []
        for f in facts.find({"user_id": user_id, "is_active": True}):
            result.append({
                "text": f.get("text"),
                "category": f.get("category"),
                "importance": f.get("importance"),
                "confidence": f.get("confidence"),
                "name": f.get("name"),
                "role": f.get("role"),
                "kind": f.get("kind"),
                "tags": f.get("tags"),
                "type": f.get("type"),
            })
        return result

    # ==================================================
    # CONSULTAS ESPECIALIZADAS
    # ==================================================
    def get_family_facts(self, user_id):
        """Retorna solos hechos con roles familiares."""
        FAMILY_ROLES = {
            "madre", "padre", "mamá", "mama", "papá", "papa",
            "hermana", "hermano",
            "abuela", "abuelo", "tía", "tia", "tio", "tío",
            "pareja", "novia", "novio", "esposa", "esposo"
        }

        res = []
        for f in facts.find({"user_id": user_id, "is_active": True}):
            role = (f.get("role") or "").lower()
            if role in FAMILY_ROLES:
                res.append(f)
        return res

    def get_family_by_role(self, user_id, role: str):
        """Ej: get_family_by_role(uid, 'abuela')"""
        return [
            f for f in facts.find({
                "user_id": user_id,
                "role": role.lower(),
                "is_active": True
            })
        ]

    def get_pets(self, user_id):
        """Retorna todas las mascotas registradas estructuradamente."""
        return [
            f for f in facts.find({
                "user_id": user_id,
                "category": "pet",
                "is_active": True
            })
        ]

    def get_relationships(self, user_id):
        """Familia + pareja + amigos importantes."""
        return [
            f for f in facts.find({
                "user_id": user_id,
                "category": "relationship",
                "is_active": True
            })
        ]

    def get_all_facts_pretty(self, user_id):
        """Para depuración — devuelve texto limpio."""
        pretty = []
        for f in self.get_facts(user_id):
            line = f"• {f.get('text')}"
            if f.get("role"):
                line += f" (rol: {f['role']})"
            if f.get("name"):
                line += f" → {f['name']}"
            if f.get("kind"):
                line += f" [{f['kind']}]"
            pretty.append(line)
        return "\n".join(pretty)

    # ==================================================
    # MEMORIA SEMÁNTICA (EMBEDDINGS)
    # ==================================================
    def add_semantic(self, user_id: str, text: str):
        IMPORTANT = [
            "me gusta", "mi comida favorita", "odio", "mi novia", "mi pareja",
            "mi mamá", "mi papá", "trabajo", "estoy estudiando", "mi sueño",
            "mi meta", "mi color favorito", "quiero lograr"
        ]
        if any(k in text.lower() for k in IMPORTANT):
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
        # --------------------------------------------------------------
    # RESUMEN FAMILIAR — usado por AuriMind._resolve_info
    # --------------------------------------------------------------
    def get_family_summary(self, user_id: str) -> str:
        """
        Devuelve un resumen corto de familiares importantes basados
        en los facts estructurados ya almacenados.
        """
        family = self.get_family_facts(user_id)

        if not family:
            return ""

        items = []
        for f in family:
            role = (f.get("role") or "").capitalize()
            name = f.get("name")
            if name and role:
                items.append(f"{role}: {name}")

        return ", ".join(items)
    def normalize_role(self, role: str):
        if not role:
            return role

        r = role.lower().strip()
        MAP = {
            "madre": "mamá",
            "mama": "mamá",
            "mamá": "mamá",
            "padre": "papá",
            "papa": "papá",
            "papá": "papá",
            "hermano": "hermano",
            "hermana": "hermana",
            "tía": "tía",
            "tia": "tía",
            "tio": "tío",
            "tío": "tío",
            "abuelo": "abuelo",
            "abuela": "abuela",
            "pareja": "pareja",
            "novia": "pareja",
            "novio": "pareja",
        }

        return MAP.get(r, r)


