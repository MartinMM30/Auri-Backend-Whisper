# ============================================================
# MIGRACIÓN DE MEMORIA LEGACY → FACTS ESTRUCTURADOS (V10.x)
# ============================================================

import re
from auribrain.memory_db import dialog_recent, facts
from auribrain.memory_orchestrator import MemoryOrchestrator

# Patrones para detectar familia / mascotas / pareja
FAMILY_PATTERNS = [
    (r"(mi mamá|mi mama|mi madre)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "madre"),
    (r"(mi papá|mi papa|mi padre)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "padre"),
    (r"(mi hermana)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "hermana"),
    (r"(mi hermano)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "hermano"),
    (r"(mi abuela)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "abuela"),
    (r"(mi abuelo)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "abuelo"),
    (r"(mi tío|mi tio)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "tio"),
    (r"(mi tía|mi tia)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "tia"),
]

PET_PATTERNS = [
    (r"(mi perro|mi perrito|mi perra|mi perrita)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "perro"),
    (r"(mi gato|mi gatito|mi gata|mi gatita)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "gato"),
]

RELATIONSHIP_PATTERNS = [
    (r"(mi novia|mi pareja|mi exnovia)\s+(se llama\s+)?([A-Za-zÁÉÍÓÚáéíóúñ]+)", "pareja"),
]


def migrate_user(user_id: str):
    """
    Extrae datos de la memoria antigua del usuario y los guarda como facts estructurados.
    """
    mem = MemoryOrchestrator()
    migrated = 0

    # Leer TODO el diálogo histórico del usuario
    cur = dialog_recent.find({"user_id": user_id})
    messages = [m["text"] for m in cur if "text" in m]

    for text in messages:
        t = text.lower()

        # ===============================
        # FAMILIA
        # ===============================
        for pattern, role in FAMILY_PATTERNS:
            m = re.search(pattern, t, re.IGNORECASE)
            if m:
                name = m.group(3).capitalize()
                mem.add_fact_structured(user_id, {
                    "text": f"Su {role} se llama {name}",
                    "category": "relationship",
                    "importance": 5,
                    "confidence": 0.95,
                    "name": name,
                    "role": role,
                    "type": "family_member",
                })
                migrated += 1

        # ===============================
        # MASCOTAS
        # ===============================
        for pattern, kind in PET_PATTERNS:
            m = re.search(pattern, t, re.IGNORECASE)
            if m:
                name = m.group(3).capitalize()
                mem.add_fact_structured(user_id, {
                    "text": f"Tiene un {kind} llamado {name}",
                    "category": "pet",
                    "importance": 4,
                    "confidence": 0.95,
                    "name": name,
                    "kind": kind,
                    "type": "pet",
                })
                migrated += 1

        # ===============================
        # PAREJA
        # ===============================
        for pattern, role in RELATIONSHIP_PATTERNS:
            m = re.search(pattern, t, re.IGNORECASE)
            if m:
                name = m.group(3).capitalize()
                mem.add_fact_structured(user_id, {
                    "text": f"Su {role} se llama {name}",
                    "category": "relationship",
                    "importance": 5,
                    "confidence": 0.95,
                    "name": name,
                    "role": role,
                    "type": "relationship",
                })
                migrated += 1

    return migrated
