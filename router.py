from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from auribrain.auri_mind import AuriMind

auri = AuriMind()
router = APIRouter()


class WeatherIn(BaseModel):
    temp: float
    description: str


class ContextUpdateRequest(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[list] = None
    user: Optional[dict] = None
    prefs: Optional[dict] = None


class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):

    if req.weather:
        print("🌦 WEATHER SYNC:", req.weather)
        auri.context.set_weather(_SimpleWeather(req.weather.temp, req.weather.description))

    if req.events:
        auri.context.set_events(req.events)

    if req.user:
        auri.context.set_user(req.user)

    if req.prefs:
        auri.context.set_prefs(req.prefs)

        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])

    return {"ok": True, "updated": True}
