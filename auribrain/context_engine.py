# auribrain/context_engine.py
from datetime import datetime
from zoneinfo import ZoneInfo


class ContextEngine:
    """
    Motor de contexto de Auri.
    - Maneja zona horaria
    - Mantiene clima, eventos, usuario y prefs
    - Expone un paquete diario para el LLM
    """

    def __init__(self, timezone: str = "UTC"):
        self.tz = self._safe_tz(timezone)

        self.weather = None           # objeto con .temp y .description
        self.next_events = []         # lista de dicts: {title, urgent, when}
        self.memory_engine = None     # se inyecta desde AuriMind

        # Nuevos: perfil de usuario + preferencias
        self.user = {
            "name": None,
            "city": None,
        }
        self.prefs = {
            "shortReplies": False,
            "softVoice": False,
            "personality": "auri_classic",
        }

    # ---------------- TZ segura ----------------
    def _safe_tz(self, tzname: str) -> ZoneInfo:
        try:
            return ZoneInfo(tzname)
        except Exception:
            print(f"[WARN] Invalid timezone '{tzname}', falling back to UTC")
            return ZoneInfo("UTC")

    def update_timezone(self, tzname: str):
        print(f"[INFO] Updating timezone → {tzname}")
        self.tz = self._safe_tz(tzname)

    # --------------- Hooks externos -------------
    def attach_memory(self, mem):
        self.memory_engine = mem

    def set_weather(self, weather_model):
        """
        Espera un objeto con atributos:
        - temp
        - description
        (lo crea router.py con _SimpleWeather)
        """
        self.weather = weather_model

    def set_events(self, events):
        self.next_events = events or []

    def set_user(self, user_dict: dict):
        """
        user_dict viene de router.py → {name, city}
        """
        if not isinstance(user_dict, dict):
            return
        name = user_dict.get("name")
        city = user_dict.get("city")

        if name:
            self.user["name"] = name
        if city:
            self.user["city"] = city

    def set_prefs(self, prefs_dict: dict):
        """
        prefs_dict → {shortReplies, softVoice, personality}
        """
        if not isinstance(prefs_dict, dict):
            return

        if "shortReplies" in prefs_dict and prefs_dict["shortReplies"] is not None:
            self.prefs["shortReplies"] = bool(prefs_dict["shortReplies"])

        if "softVoice" in prefs_dict and prefs_dict["softVoice"] is not None:
            self.prefs["softVoice"] = bool(prefs_dict["softVoice"])

        personality = prefs_dict.get("personality")
        if personality:
            self.prefs["personality"] = personality

    # ----------------- Derivados ----------------
    def get_time_of_day(self) -> str:
        now = datetime.now(self.tz)
        h = now.hour
        if 5 <= h < 12:
            return "morning"
        if 12 <= h < 18:
            return "afternoon"
        if 18 <= h < 23:
            return "evening"
        return "night"

    def weather_summary(self) -> str:
        if not self.weather:
            return "unknown"
        w = self.weather
        # Asume atributos .temp y .description
        return f"{w.temp}°C, {w.description}"

    def next_event_summary(self) -> str:
        if not self.next_events:
            return "No upcoming events"
        return ", ".join(e.get("title", "event") for e in self.next_events[:3])

    def workload_level(self) -> str:
        if not self.next_events:
            return "light"

        urgent = len([e for e in self.next_events if e.get("urgent")])
        total = len(self.next_events)

        if urgent > 2:
            return "overloaded"
        if total > 4:
            return "busy"
        return "light"

    def estimate_energy(self) -> str:
        if not self.memory_engine:
            return "normal"
        emo = self.memory_engine.get_emotion()
        return {
            "happy": "high",
            "tired": "low",
            "sad": "very_low",
        }.get(emo, "normal")

    # ------------- Paquete final de contexto ------------
    def get_daily_context(self) -> dict:
        now = datetime.now(self.tz)
        return {
            "datetime": now.isoformat(),
            "time_of_day": self.get_time_of_day(),
            "timezone": str(self.tz),
            "weather": self.weather_summary(),
            "next_events": self.next_event_summary(),
            "workload": self.workload_level(),
            "energy": self.estimate_energy(),
            "emotion": self.memory_engine.get_emotion() if self.memory_engine else "neutral",
            "recent_messages": self.memory_engine.get_recent() if self.memory_engine else [],
            "life_events": self.memory_engine.get_narrative_summary() if self.memory_engine else [],
            # 👇 estos dos son clave para clima + perfil
            "user": self.user,
            "prefs": self.prefs,
        }
