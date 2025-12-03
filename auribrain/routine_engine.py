# auribrain/routine_engine.py

class RoutineEngine:
    """Modo Rutinas Inteligentes – propone pequeñas rutinas según estado emocional y agenda."""

    def detect(self, ctx: dict, emotion_snapshot: dict) -> str | None:
        stress = emotion_snapshot.get("stress", 0.3)
        energy = emotion_snapshot.get("energy", 0.5)
        events = ctx.get("events", []) or []

        if stress > 0.7:
            return "stress_routine"
        if energy < 0.3:
            return "fatigue_routine"
        if len(events) >= 10:
            return "busy_day"

        return None

    def respond(self, mode: str) -> str:
        if mode == "stress_routine":
            return (
                "Te noto muy cargado. Hagamos una mini-rutina anti-estrés:\n"
                "• 5 minutos de respiración\n"
                "• 10 minutos para vos\n"
                "• Luego vemos pendientes\n"
                "¿Querés que lo guarde como recordatorio?"
            )

        if mode == "fatigue_routine":
            return (
                "Hoy estás realmente agotado. Sugiero:\n"
                "• Una tarea pequeña\n"
                "• Cena ligera\n"
                "• Dormir un poco más temprano\n"
                "¿Querés un recordatorio para mañana?"
            )

        if mode == "busy_day":
            return (
                "Tu día está bastante lleno. Vamos a priorizar solo 3 cosas clave.\n"
                "Decime cuál es la #1 para vos."
            )

        return ""
