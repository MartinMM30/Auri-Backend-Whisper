# api/memory_router.py

from fastapi import APIRouter
from auribrain.memory_orchestrator import MemoryOrchestrator
from auribrain.memory_db import users, facts, dialog_recent, memory_vectors

router = APIRouter(prefix="/memory", tags=["Memory"])
mem = MemoryOrchestrator()

# ======================================================
# USER PROFILE
# ======================================================

@router.get("/profile/{user_id}")
def get_profile(user_id: str):
    return {"profile": mem.get_user_profile(user_id)}


@router.post("/profile/{user_id}")
def update_profile(user_id: str, data: dict):
    mem.update_user_profile(user_id, data)
    return {"status": "updated", "data": data}


# ======================================================
# FACTUAL MEMORY
# ======================================================

@router.get("/facts/{user_id}")
def get_facts(user_id: str):
    return {"facts": mem.get_facts(user_id)}


@router.post("/facts/{user_id}")
def add_fact(user_id: str, fact: str):
    mem.add_fact(user_id, fact)
    return {"status": "saved", "fact": fact}


# ======================================================
# SEMANTIC MEMORY (EMBEDDINGS)
# ======================================================

@router.post("/semantic/{user_id}")
def add_semantic(user_id: str, text: str):
    mem.add_semantic(user_id, text)
    return {"status": "semantic_saved", "text": text}


@router.get("/semantic/{user_id}")
def search_semantic(user_id: str, q: str):
    results = mem.search_semantic(user_id, q)
    return {"results": results}


# ======================================================
# RECENT DIALOG MEMORY
# ======================================================

@router.get("/dialog/{user_id}")
def recent_dialog(user_id: str, n: int = 10):
    return {"dialog": mem.get_recent_dialog(user_id, n)}


@router.post("/dialog/{user_id}")
def add_dialog(user_id: str, role: str, text: str):
    mem.add_dialog(user_id, role, text)
    return {"status": "dialog_saved"}


# ======================================================
# CLEAR MEMORY
# ======================================================

@router.delete("/clear/all/{user_id}")
def clear_all(user_id: str):

    users.delete_one({"_id": user_id})
    facts.delete_many({"user_id": user_id})
    dialog_recent.delete_many({"user_id": user_id})
    memory_vectors.delete_many({"user_id": user_id})

    return {"status": "ALL memory cleared for user", "user": user_id}


# ======================================================
# 🔍 DEBUG: ESTADO MENTAL COMPLETO DEL USUARIO
# ======================================================

@router.get("/debug/{user_id}")
def debug_memory(user_id: str):

    return {
        "profile": mem.get_user_profile(user_id),
        "facts": mem.get_facts(user_id),
        "recent_dialog": mem.get_recent_dialog(user_id, 20),
        "semantic_memory_count": memory_vectors.count_documents({"user_id": user_id}),
        "semantic_samples": [
            d.get("text") for d in memory_vectors.find({"user_id": user_id}).limit(5)
        ],
    }
