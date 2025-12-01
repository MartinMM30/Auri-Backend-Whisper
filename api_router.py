from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()


class WeatherIn(BaseModel):
    temp: float
    description: str


class ContextUpdateRequest(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[List[Dict[str, Any]]] = None
    user: Optional[Dict[str, Any]] = None  # acepta TODO el user de Flutter
    prefs: Optional[Dict[str, Any]] = None


class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):



    print("\n================ CONTEXT SYNC RECIBIDO ================")
    print(req.dict())
    print("=======================================================\n")

    # VALIDAR BLOQUES DEL PAYLOAD
    blocks_ok = True

    # WEATHER
    if req.weather:
        auri.context.set_weather(_SimpleWeather(
            req.weather.temp,
            req.weather.description,
        ))
    else:
        blocks_ok = False

    # EVENTS
    if req.events is not None:
        auri.context.set_events(req.events)
    else:
        blocks_ok = False

    # USER
    if req.user is not None and "name" in req.user:
        auri.context.set_user(req.user)
    else:
        blocks_ok = False

    # PREFS
    if req.prefs is not None:
        auri.context.set_prefs(req.prefs)
        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])
    else:
        blocks_ok = False

    # ------------------------------------------
    # SOLO MARCAR READY SI TODO EL PERFIL ESTÁ
    # ------------------------------------------
    if blocks_ok:
        auri.context.mark_ready()
        print("✔ CONTEXTO LISTO → ready = True")
    else:
        print("✘ CONTEXTO INCOMPLETO → ready = False")

    return {"ok": True}
