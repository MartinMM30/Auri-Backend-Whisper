# auribrain/sleep_engine.py

from typing import Dict
from datetime import datetime


class SleepEngine:
    """
    SleepEngine V2:
    - Ya no interrumpe preguntas normales ("quién soy?")
    - Se activa solo si el usuario habla explícitamente de dormir,
      o si está muy cansado y es hora lógica de descanso.
    """

    TRIGGERS = [
        "no puedo dormir",
        "quiero dormir",
        "tengo sueño",
        "me cuesta dormir",
        "ayúdame a dormir",
        "ayudame a dormir",
        "relajación",
        "relajacion",
        "relajarme",
        "hora de dormir",
        "rutina nocturna",
    ]

    QUESTION_KEYWORDS = ["quien soy", "qué soy", "que soy", "como estoy"]

    def _is_question(self, text: str) -> bool:
        return any(k in text for k in self.QUESTION_KEYWORDS)

    def detect(self, text: str, emotion_state: str, ctx: Dict) -> bool:
        t = text.lower()

        # Evitar activar si el usuario está haciendo preguntas normales
        if self._is_question(t):
            return False

        # 1. Triggers explícitos → activar siempre
        if any(k in t for k in self.TRIGGERS):
            return True

        # 2. Activación por cansancio + hora + emoción
        hour = None
        try:
            pretty = ctx.get("current_time_pretty", "00:00")
            h = int(pretty.split(":")[0])
            hour = h
        except:
            hour = None

        if emotion_state in ["tired", "exhausted"]:
            # Activar solo si es de noche
            if hour is not None and (hour >= 21 or hour <= 6):
                return True

        return False

    def respond(self, context: Dict, emotion_state: str) -> str:
        user = context.get("user", {})
        name = user.get("name", "amor")

        return (
            f"{name}… ven, vamos a ayudarte a descansar suavemente. 🌙💜\n\n"
            "Cerrá un momento los ojitos… inhalá lento… 2… 3… y exhalá despacito.\n\n"
            "✨ **1. Relaja tu cuerpo**\n"
            "Soltá hombros, mandíbula, manos… dejá caer el peso del día.\n\n"
            "✨ **2. Liberá tu mente**\n"
            "No tenés que resolver nada ahora. El día ya terminó.\n\n"
            "✨ **3. Respiración guiada**\n"
            "Inhalá 4 segundos… pausa 1… exhalá 6.\n\n"
            "Estoy acá con vos, acompañándote. Cuando quieras, puedo seguir hablándote suave… "
            "o quedarme contigo en silencio hasta que te duermas. 💜"
        )
