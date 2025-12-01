from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()


# ================== MODELOS ==================

class WeatherIn(BaseModel):
    temp: float
    description: str


class ContextUpdateRequest(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[List[Dict[str, Any]]] = None
    classes: Optional[List[Dict[str, Any]]] = None
    exams: Optional[List[Dict[str, Any]]] = None
    birthdays: Optional[List[Dict[str, Any]]] = None
    payments: Optional[List[Dict[str, Any]]] = None
    user: Optional[Dict[str, Any]] = None
    prefs: Optional[Dict[str, Any]] = None


# Simple adapter
class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


# ================== ENDPOINT ==================

@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):
    print("\n================ CONTEXT SYNC RECIBIDO ================")
    print(req.dict())
    print("=======================================================\n")

    ctx = auri.context
    ctx.invalidate()  # siempre invalidamos antes de validar

    blocks_ok = True

    # WEATHER
    if req.weather:
        ctx.set_weather(_SimpleWeather(req.weather.temp, req.weather.description))
    else:
        blocks_ok = False

    # EVENTS
    if req.events is not None:
        ctx.set_events(req.events)
    else:
        blocks_ok = False

    # CLASSES
    if req.classes is not None:
        ctx.set_classes(req.classes)
    else:
        blocks_ok = False

    # EXAMS
    if req.exams is not None:
        ctx.set_exams(req.exams)
    else:
        blocks_ok = False

    # BIRTHDAYS
    if req.birthdays is not None:
        ctx.set_birthdays(req.birthdays)
    else:
        blocks_ok = False

    # PAYMENTS
    if req.payments is not None:
        ctx.set_payments(req.payments)
    else:
        blocks_ok = False

    # USER
    if req.user and "name" in req.user:
        ctx.set_user(req.user)
    else:
        blocks_ok = False

    # PREFS
    if req.prefs is not None:
        ctx.set_prefs(req.prefs)
        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])
    else:
        blocks_ok = False

    # READY CHECK
    if blocks_ok:
        ctx.mark_ready()
        print("✔ CONTEXTO COMPLETO — ready = True")
    else:
        print("✘ CONTEXTO INCOMPLETO — ready = False")

    return {"ok": True}
