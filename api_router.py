from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from auribrain.auri_singleton import auri
from realtime.realtime_broadcast import realtime_broadcast
from auribrain.memory_db import users
from datetime import datetime


router = APIRouter()

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

    # 🔥 Nuevos campos críticos
    timezone: Optional[str] = None
    current_time_iso: Optional[str] = None
    current_time_pretty: Optional[str] = None
    current_date_pretty: Optional[str] = None

    class Config:
        extra = "allow"


class _SimpleWeather:
    def __init__(self, temp, description):
        self.temp = temp
        self.description = description


# ================== ENDPOINT ==================

@router.post("/context/sync")
async def context_sync(req: ContextUpdateRequest):
    data = req.dict()

    # 🔥 LEER UID desde raíz del JSON
    firebase_uid = data.get("firebase_uid", None)

    print("\n================ CONTEXT SYNC RECIBIDO ================")
    print(data)
    print("UID detectado:", firebase_uid)
    print("=======================================================\n")

    ctx = auri.context
    ctx.invalidate()
    blocks_ok = True

    # -----------------------------
    #  WEATHER
    # -----------------------------
    if req.weather:
        ctx.set_weather(_SimpleWeather(req.weather.temp, req.weather.description))
    else:
        blocks_ok = False

    # -----------------------------
    #  EVENTS
    # -----------------------------
    if req.events is not None:
        ctx.set_events(req.events)
    else:
        blocks_ok = False

    # -----------------------------
    #  CLASSES
    # -----------------------------
    if req.classes is not None:
        ctx.set_classes(req.classes)
    else:
        blocks_ok = False

    # -----------------------------
    #  EXAMS
    # -----------------------------
    if req.exams is not None:
        ctx.set_exams(req.exams)
    else:
        blocks_ok = False

    # -----------------------------
    #  BIRTHDAYS
    # -----------------------------
    if req.birthdays is not None:
        ctx.set_birthdays(req.birthdays)
    else:
        blocks_ok = False

    # -----------------------------
    #  PAYMENTS
    # -----------------------------
    if req.payments is not None:
        ctx.set_payments(req.payments)
    else:
        blocks_ok = False

    # -----------------------------
    #  USER + UID
    # -----------------------------
    if req.user:

        # 🔥 insertar UID dentro del user-block
        if firebase_uid:
            req.user["firebase_uid"] = firebase_uid

        ctx.set_user(req.user)

        # 🔥 guardar perfil en Mongo SOLO si hay login real
        if firebase_uid:
            users.update_one(
                {"_id": firebase_uid},
                {
                    "$set": {
                        "name": req.user.get("name"),
                        "city": req.user.get("city"),
                        "occupation": req.user.get("occupation"),
                        "birthday": req.user.get("birthday"),
                        "context": data,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
    else:
        blocks_ok = False

    # -----------------------------
    #  PREFS
    # -----------------------------
    if req.prefs is not None:
        ctx.set_prefs(req.prefs)
        if "personality" in req.prefs:
            auri.personality.set_personality(req.prefs["personality"])
    else:
        blocks_ok = False

    # -----------------------------
    #  TIMEZONE + TIME INFO
    # -----------------------------
    if req.timezone:
        ctx.set_timezone(req.timezone)

    if req.current_time_iso or req.current_time_pretty or req.current_date_pretty:
        ctx.set_time_info(
            iso=req.current_time_iso,
            pretty=req.current_time_pretty,
            date=req.current_date_pretty
        )

    # -----------------------------
    #  READY
    # -----------------------------
    if blocks_ok:
        ctx.mark_ready()
        print("✔ CONTEXTO COMPLETO — ready = True")
        await realtime_broadcast.broadcast({"type": "context_ready"})
    else:
        print("✘ CONTEXTO INCOMPLETO — ready = False")

    return {"ok": True, "uid_used": firebase_uid}
