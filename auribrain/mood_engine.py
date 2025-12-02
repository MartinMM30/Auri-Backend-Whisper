# auribrain/mood_engine.py

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MoodState:
    mood: str       # "neutral", "happy", "concerned", "strict"
    intensity: float  # 0.0 - 1.0
    voice_id: str   # "alloy", "nova", etc.
    style: str      # "auri_classic", "soft", "anime", etc.


class MoodEngine:
    """
    Versión simple: reglas por palabras clave.
    Luego puedes cambiar a LLM si quieres.
    """

    def infer(self, user_msg: str, context: Dict[str, Any]) -> MoodState:
        t = (user_msg or "").lower()

        # Muy feliz / agradecido
        if any(k in t for k in ["gracias", "te quiero", "me encanta", "eres genial"]):
            return MoodState(
                mood="happy",
                intensity=0.8,
                voice_id="alloy",
                style="auri_soft",
            )

        # Cansado / triste / estresado
        if any(k in t for k in ["cansado", "triste", "estresado", "agotado"]):
            return MoodState(
                mood="concerned",
                intensity=0.9,
                voice_id="nova",
                style="auri_calm",
            )

        # Modo más serio / productivo
        if any(k in t for k in ["concentrado", "estudiar", "trabajar", "enfocado"]):
            return MoodState(
                mood="focused",
                intensity=0.7,
                voice_id="verse",
                style="auri_pro",
            )

        # Default
        return MoodState(
            mood="neutral",
            intensity=0.3,
            voice_id="alloy",
            style="auri_classic",
        )
