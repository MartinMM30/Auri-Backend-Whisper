# router.py
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from auribrain.auri_mind import AuriMind

auri = AuriMind()
router = APIRouter()

# ---------------- Modelos ----------------

class ThinkRequest(BaseModel):
    message: str

class ThinkResponse(BaseModel):
    intent: str
    raw: str
    final: str

class TimezoneRequest(BaseModel):
    timezone: str

class PersonalitySetRequest(BaseModel):
    key: str

class MemoryRememberRequest(BaseModel):
    key: str
    value: str

# EVENTOS
class EventIn(BaseModel):
    title: str
    urgent: bool = False
    when: Optional[str] = None

# CLIMA
class WeatherIn(BaseModel):
    temp: float
    description: str

# USER
class UserIn(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None

# PREFS
class PrefsIn(BaseModel):
    shortReplies: Optional[bool] = False
    softVoice: Optional[bool] = False
    personality: Optional[str] = "auri_classic"

# CONTEXTO COMPLETO
class ContextUpdateRequest(BaseModel):
    weather: Optional[WeatherIn] = None
    events: Optional[List[EventIn]] = None
    user: Optional[UserIn] = None
    prefs: Optional[PrefsIn] = None

# Adaptador clima
class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


# ---------------- THINK ----------------

@router.post("/think", response_model=ThinkResponse)
async def think(req: ThinkRequest):
    result = auri.think(req.message)
    return ThinkResponse(
        intent=result.get("intent", "unknown"),
        raw=result.get("raw", ""),
        final=result.get("final", ""),
    )


# ---------------- TIMEZONE ----------------

@router.post("/timezone/set")
async def set_timezone(req: TimezoneRequest):
    auri.context.update_timezone(req.timezone)
    return {"ok": True, "timezone": str(auri.context.tz)}


# ---------------- PERSONALIDAD ----------------

@router.post("/personality/set")
async def set_personality(req: PersonalitySetRequest):
    auri.personality.set_personality(req.key)
    style = auri.personality.get_style()
    return {"ok": True, "active": req.key, "tone": style["tone"], "traits": style["traits"]}

@router.get("/personality/get")
async def get_personality():
    style = auri.personality.get_style()
    return {"active": auri.personality.current, "tone": style["tone"], "traits": style["traits"]}


# ---------------- MEMORIA ----------------

@router.post("/memory/remember")
async def remember(req: MemoryRememberRequest):
    auri.memory.remember(req.key, req.value)
    return {"ok": True}

@router.get("/memory/profile")
async def get_profile():
    return auri.memory.get_profile()


# ---------------- CONTEXTO ----------------

@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):

    # WEATHER
    if req.weather:
        auri.context.set_weather(
            _SimpleWeather(req.weather.temp, req.weather.description)
        )

    # EVENTS
    if req.events:
        parsed = []
        for e in req.events:
            parsed.append({
                "title": e.title,
                "urgent": e.urgent,
                "when": e.when
            })
        auri.context.set_events(parsed)

    # USER
    if req.user:
        auri.context.set_user({
            "name": req.user.name,
            "city": req.user.city,
        })

    # PREFS
    if req.prefs:
        auri.context.set_prefs({
            "shortReplies": req.prefs.shortReplies,
            "softVoice": req.prefs.softVoice,
            "personality": req.prefs.personality,
        })

        # Aplicar personalidad automáticamente
        if req.prefs.personality:
            auri.personality.set_personality(req.prefs.personality)

    return {"ok": True, "updated": True}


@router.get("/context/debug")
async def debug_context():
    return auri.context.get_daily_context()
