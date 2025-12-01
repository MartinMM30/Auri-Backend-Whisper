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

    if req.weather:
        auri.context.set_weather(_SimpleWeather(
            req.weather.temp,
            req.weather.description,
        ))

    if req.events:
        auri.context.set_events(req.events)

    if req.user:
        auri.context.set_user(req.user)

    if req.prefs:
        auri.context.set_prefs(req.prefs)
        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])

    return {"ok": True}
