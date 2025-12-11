from fastapi import APIRouter
from auribrain.migrate_legacy_memory import run_memory_migration

router = APIRouter()

@router.post("/run-memory-migration")
async def run_migration():
    result = run_memory_migration()
    return {"status": "ok", "details": result}
