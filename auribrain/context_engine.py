# auribrain/context_engine.py

from datetime import datetime
from typing import Any, Dict, List


class ContextEngine:

    def __init__(self):
        # UID del usuario autenticado (WEBsocket)
        self._active_uid = None

        # USER
        self.user = {
            "name": None,
            "city": None,
            "birthday": None,
            "occupation": None,
            "firebase_uid": None,
        }

        # WEATHER
        self.weather = {
            "temp": None,
            "description": None,
            "timestamp": None,
        }

        # AGENDA
        self.events: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.exams: List[Dict[str, Any]] = []
        self.birthdays: List[Dict[str, Any]] = []
        self.payments: List[Dict[str, Any]] = []

        # PREFS
        self.prefs = {
            "shortReplies": False,
            "softVoice": False,
            "personality": "auri_classic",
        }

        # TIMEZONE
        self.tz = "UTC"

        # TIME / DATE
        self.current_time_iso = None
        self.current_time_pretty = None
        self.current_date_pretty = None

        # Ready flag
        self.ready_flag = False



    # ===========================================================
    # 🔐 UID desde WebSocket
    # ===========================================================
    def set_user_uid(self, uid: str):
        """ Guarda UID del usuario y lo mete al bloque user """
        self._active_uid = uid
        self.user["firebase_uid"] = uid
        print(f"[ContextEngine] UID registrado en contexto: {uid}")

    def get_user_uid(self):
        return self._active_uid



    # ===========================================================
    # SETTERS PARA SÍNCRO DE CONTEXTO
    # ===========================================================
    def set_weather(self, w):
        self.weather = {
            "temp": getattr(w, "temp", None),
            "description": getattr(w, "description", None),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def set_user(self, data: Dict[str, Any]):
        for k in ["name", "city", "birthday", "occupation"]:
            if k in data:
                self.user[k] = data[k]

        # No borrar UID si ya lo tenemos
        if "firebase_uid" in data and data["firebase_uid"]:
            self.user["firebase_uid"] = data["firebase_uid"]

    def set_events(self, events):
        self.events = events or []

    def set_classes(self, classes):
        self.classes = classes or []

    def set_exams(self, exams):
        self.exams = exams or []

    def set_birthdays(self, bds):
        self.birthdays = bds or []

    def set_payments(self, payments):
        self.payments = payments or []

    def set_prefs(self, prefs):
        for k in self.prefs.keys():
            if k in prefs:
                self.prefs[k] = prefs[k]

    def set_timezone(self, tz: str):
        self.tz = tz

    def set_time_info(self, iso=None, pretty=None, date=None):
        if iso:
            self.current_time_iso = iso
        if pretty:
            self.current_time_pretty = pretty
        if date:
            self.current_date_pretty = date



    # ===========================================================
    # READY CONTROL
    # ===========================================================
    def is_ready(self) -> bool:
        return self.ready_flag

    def mark_ready(self):
        self.ready_flag = True

    def invalidate(self):
        self.ready_flag = False



    # ===========================================================
    # CONTEXTO FINAL PARA AURIMIND
    # ===========================================================
    def get_daily_context(self):
        return {
            "user": self.user,
            "weather": self.weather,
            "events": self.events,
            "classes": self.classes,
            "exams": self.exams,
            "birthdays": self.birthdays,
            "payments": self.payments,
            "prefs": self.prefs,
            "timezone": self.tz,
            "current_time_iso": self.current_time_iso,
            "current_time_pretty": self.current_time_pretty,
            "current_date_pretty": self.current_date_pretty,
            "ready": self.ready_flag,
        }
