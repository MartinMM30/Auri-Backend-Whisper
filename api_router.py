# api_router.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from auribrain.auri_mind import AuriMind

# instancia global
auri = AuriMind()

# ESTE router es el que se importa desde server.py
router = APIRouter()


# -----------------------------
# MODELOS DE ENTRADA
# -----------------------------
class WeatherIn(BaseModel):
    temp: float
    description: str


class ContextUpdateRequest(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[List[Dict[str, Any]]] = None
    user: Optional[Dict[str, Any]] = None
    prefs: Optional[Dict[str, Any]] = None


# Clase interna solo para mapear datos del clima
class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


# -----------------------------
# ENDPOINT PRINCIPAL
# -----------------------------
@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):
    """
    Recibe datos desde Flutter:
      - weather
      - user
      - events
      - prefs
    Y actualiza el contexto global de AuriMind.
    """

    if req.weather:
        print(f"🌦 WEATHER SYNC: temp={req.weather.temp} desc='{req.weather.description}'")
        w = _SimpleWeather(req.weather.temp, req.weather.description)
        auri.context.set_weather(w)

    if req.events:
        auri.context.set_events(req.events)

    if req.user:
        auri.context.set_user(req.user)

    if req.prefs:
        auri.context.set_prefs(req.prefs)

        # Si viene personalidad → actualizar motor
        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])

    return {"status": "ok", "updated": True}
