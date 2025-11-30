# auribrain/context_engine.py
from datetime import datetime
from zoneinfo import ZoneInfo

class ContextEngine:
    """
    Motor de contexto de Auri.
    Soporta:
    - clima
    - eventos (pagos, clases, deadlines, cumpleaños)
    - usuario (nombre, ciudad)
    - preferencias (voz, estilo, personalidad)
    - memoria emocional
    """

    def __init__(self, timezone: str = "UTC"):
        self.tz = self._safe_tz(timezone)

        self.weather = None
        self.next_events = []
        self.memory_engine = None

        self.user = {"name": None, "city": None}
        self.prefs = {
            "shortReplies": False,
            "softVoice": False,
            "personality": "auri_classic"
        }

    # ---------------- TZ segura ----------------
    def _safe_tz(self, tzname: str) -> ZoneInfo:
        try:
            return ZoneInfo(tzname)
        except Exception:
            print(f"[WARN] Invalid timezone '{tzname}', falling back to UTC")
            return ZoneInfo("UTC")

    def update_timezone(self, tzname: str):
        self.tz = self._safe_tz(tzname)

    # ---------------- Hooks externos ----------------
    def attach_memory(self, mem):
        self.memory_engine = mem

    # ---------------- WEATHER ----------------
    def set_weather(self, weather_model):
        self.weather = weather_model

    # ---------------- EVENTS ----------------
    def set_events(self, events):
        normalized = []

        for e in events:
            iso = e.get("when")
            when_dt = None

            try:
                if iso:
                    when_dt = datetime.fromisoformat(iso)
            except:
                when_dt = None

            normalized.append({
                "title": e.get("title", "event"),
                "urgent": bool(e.get("urgent", False)),
                "when": when_dt
            })

        self.next_events = normalized

    # ---------------- USER ----------------
    def set_user(self, user_dict):
        self.user = {
            "name": user_dict.get("name"),
            "city": user_dict.get("city")
        }

    # ---------------- PREFS ----------------
    def set_prefs(self, prefs_dict):
        self.prefs = {
            "shortReplies": prefs_dict.get("shortReplies", False),
            "softVoice": prefs_dict.get("softVoice", False),
            "personality": prefs_dict.get("personality", "auri_classic")
        }

    # ---------------- Derivados ----------------
    def get_time_of_day(self) -> str:
        now = datetime.now(self.tz)
        h = now.hour

        if 5 <= h < 12: return "morning"
        if 12 <= h < 18: return "afternoon"
        if 18 <= h < 23: return "evening"
        return "night"

    def weather_summary(self) -> str:
        if not self.weather:
            return "unknown"
        return f"{self.weather.temp}°C, {self.weather.description}"

    def next_event_summary(self) -> str:
        if not self.next_events:
            return "No upcoming events"

        events = [e for e in self.next_events if e["when"]]
        if not events:
            return "No upcoming events"

        events.sort(key=lambda e: e["when"])
        titles = [e["title"] for e in events[:3]]
        return ", ".join(titles)

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

    # ---------------- Paquete final ----------------
    def get_daily_context(self) -> dict:
        now = datetime.now(self.tz)

        return {
            "datetime": now.isoformat(),

            "user": self.user,
            "prefs": self.prefs,

            "weather": self.weather_summary(),
            "time_of_day": self.get_time_of_day(),
            "next_events": self.next_event_summary(),
            "workload": self.workload_level(),
            "energy": self.estimate_energy(),

            "emotion": self.memory_engine.get_emotion() if self.memory_engine else "neutral",
            "recent_messages": self.memory_engine.get_recent() if self.memory_engine else [],
            "life_events": self.memory_engine.get_narrative_summary() if self.memory_engine else [],
        }
