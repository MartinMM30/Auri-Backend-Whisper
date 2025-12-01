# routes/context_sync.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()

class WeatherIn(BaseModel):
    temp: float
    description: str

class ContextPayload(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[List[Dict[str, Any]]] = None
    user: Optional[Dict[str, Any]] = None
    prefs: Optional[Dict[str, Any]] = None
    classes: Optional[List[Dict[str, Any]]] = None
    exams: Optional[List[Dict[str, Any]]] = None
    birthdays: Optional[List[Dict[str, Any]]] = None
    payments: Optional[List[Dict[str, Any]]] = None


class SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


@router.post("/sync")
async def sync_context(data: ContextPayload):

    if data.weather:
        auri.context.set_weather(SimpleWeather(
            data.weather.temp,
            data.weather.description
        ))

    if data.events:
        auri.context.set_events(data.events)

    if data.payments:
        auri.context.set_bills(data.payments)

    if data.user:
        auri.context.set_user(data.user)

    if data.prefs:
        auri.context.set_prefs(data.prefs)
        if "personality" in data.prefs:
            auri.personality.set_personality(data.prefs["personality"])

    return {"ok": True}
