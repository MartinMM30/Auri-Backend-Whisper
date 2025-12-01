from datetime import datetime
from typing import Any, Dict, List


class ContextEngine:

    def __init__(self):
        self.memory = None

        # USER
        self.user = {
            "name": None,
            "city": None,
            "birthday": None,
            "occupation": None,
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

        # READY FLAG
        self.ready_flag = False

    # =====================================================
    def attach_memory(self, memory):
        self.memory = memory

    # =====================================================
    # SETTERS
    # =====================================================
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

    def update_timezone(self, tz):
        self.tz = tz

    # =====================================================
    # READY CONTROL
    # =====================================================
    def is_ready(self) -> bool:
        return self.ready_flag

    def mark_ready(self):
        self.ready_flag = True

    def invalidate(self):
        self.ready_flag = False

    # =====================================================
    # FINAL PAYLOAD (para LLM)
    # =====================================================
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
            "ready": self.ready_flag,
        }
