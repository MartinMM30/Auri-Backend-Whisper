# auribrain/context_engine.py
from datetime import datetime
from zoneinfo import ZoneInfo

class ContextEngine:
    """
    Motor de contexto de Auri.
    - Usa zona horaria configurable (por defecto UTC).
    - Puede actualizar la TZ desde Flutter (update_timezone).
    - Expone un resumen diario para que la mente de Auri responda mejor.
    """

    def __init__(self, timezone: str = "UTC"):
        self.tz = self._safe_tz(timezone)

        self.weather = None
        self.next_events = []
        self.memory_engine = None

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
        self.weather = weather_model

    def set_events(self, events):
        self.next_events = events or []

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
        # Asume atributos .temp y .description, ajusta si tu modelo cambia
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
        }
