from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class ContextEngine:

    def __init__(self):
        self.memory = None

        # ------- DATOS CORE -------
        self.user = {
            "name": None,
            "city": None,
            "birthday": None,
        }

        # ------- CLIMA -------
        self.weather = {
            "temp": None,
            "description": None,
            "timestamp": None
        }

        # ------- EVENTOS / AGENDA -------
        # Lista de:
        # { "title": "...", "when": "ISO", "urgent": False }
        self.events = []

        # ------- PAGOS -------
        # Lista de:
        # { "title": "...", "amount": X, "due": "ISO" }
        self.bills = []

        # ------- PREFERENCIAS -------
        self.prefs = {
            "shortReplies": False,
            "softVoice": False,
            "personality": "auri_classic",
        }

        # ------- ZONA HORARIA -------
        self.tz = "UTC"


    # ====================================================
    # CONFIG
    # ====================================================
    def attach_memory(self, memory):
        self.memory = memory


    # ====================================================
    # SETTERS
    # ====================================================
    def set_weather(self, w):
        self.weather = {
            "temp": getattr(w, "temp", None),
            "description": getattr(w, "description", None),
            "timestamp": datetime.utcnow().isoformat()
        }

    def set_user(self, user_dict: Dict[str, Any]):
        for key in ["name", "city", "birthday", "occupation"]:
            if key in user_dict:
                self.user[key] = user_dict[key]


    def set_events(self, events_list):
        self.events = events_list or []

    def set_bills(self, bills_list):
        self.bills = bills_list or []

    def set_prefs(self, prefs_dict):
        for key in self.prefs.keys():
            if key in prefs_dict:
                self.prefs[key] = prefs_dict[key]

    def update_timezone(self, tz: str):
        self.tz = tz


    # ====================================================
    # GETTERS
    # ====================================================
    def get_today_events(self):
        today = datetime.utcnow().date()
        return [
            e for e in self.events
            if e.get("when") and datetime.fromisoformat(e["when"]).date() == today
        ]

    def get_upcoming_events(self):
        now = datetime.utcnow()
        return [
            e for e in self.events
            if e.get("when") and datetime.fromisoformat(e["when"]) > now
        ]

    def get_due_bills(self):
        now = datetime.utcnow()
        return [
            b for b in self.bills
            if b.get("due") and datetime.fromisoformat(b["due"]) >= now
        ]

    # ====================================================
    # CONTEXTO COMPLETO (para response / LLM)
    # ====================================================
    def get_daily_context(self):
        return {
            "user": self.user,
            "weather": self.weather,
            "events": self.events,
            "bills": self.bills,
            "prefs": self.prefs,
            "timezone": self.tz,
        }
