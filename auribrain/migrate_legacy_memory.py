# auribrain/migrate_legacy_memory.py

"""
Migrador de memoria legado → memoria estructurada.
Versión segura y sin duplicados.
"""

from auribrain.memory_db import facts, users, dialog_recent
import datetime


def run_memory_migration():
    """
    Ejecuta la migración de cualquier memoria antigua (si existe)
    a la estructura nueva de MemoryOrchestrator.

    Si ya fue migrado previamente, no hace nada.
    """

    result = {
        "migrated_facts": 0,
        "skipped": 0,
        "status": "ok"
    }

    # ------------
    # EJEMPLO de memoria antigua a convertir
    # Supongamos que antes tenías una colección 'legacy_memory'
    # Si NO existe, simplemente devolvemos la estructura vacía.
    # ------------
    try:
        from auribrain.memory_db import legacy_memory
    except Exception:
        result["status"] = "no_legacy_memory_collection"
        return result

    cursor = legacy_memory.find({})
    for item in cursor:
        text = item.get("text")
        user_id = item.get("user_id")

        if not text or not user_id:
            result["skipped"] += 1
            continue

        # Evitar duplicados
        exists = facts.find_one({
            "user_id": user_id,
            "text": text,
            "is_active": True
        })

        if exists:
            result["skipped"] += 1
            continue

        facts.insert_one({
            "user_id": user_id,
            "text": text,
            "category": "other",
            "importance": 2,
            "confidence": 0.7,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "is_active": True
        })

        result["migrated_facts"] += 1

    return result
