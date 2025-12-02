# auribrain/memory_router.py

from fastapi import APIRouter
from pydantic import BaseModel
from auribrain.memory_orchestrator import MemoryOrchestrator

router = APIRouter(prefix="/memory", tags=["memory"])
mem = MemoryOrchestrator()

class FactIn(BaseModel):
    user_id: str
    fact: str

class DialogIn(BaseModel):
    user_id: str
    role: str
    text: str

class SemanticSearchIn(BaseModel):
    user_id: str
    query: str

@router.post("/add_fact")
def add_fact(req: FactIn):
    mem.add_fact(req.user_id, req.fact)
    return {"ok": True}

@router.post("/add_dialog")
def add_dialog(req: DialogIn):
    mem.add_dialog(req.user_id, req.role, req.text)
    return {"ok": True}

@router.post("/semantic_search")
def sem_search(req: SemanticSearchIn):
    res = mem.search_semantic(req.user_id, req.query)
    return {"results": res}
