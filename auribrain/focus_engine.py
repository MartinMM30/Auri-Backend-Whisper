# auribrain/focus_engine.py

from datetime import datetime
from typing import Dict, Any


class FocusEngine:
    """
    Ayuda al usuario a enfocarse, estudiar o trabajar.
    Divide tareas grandes, reduce ansiedad y da estructura.
    """

    TRIGGERS = [
        "no sé qué hacer", "no se que hacer",
        "tengo mucho", "demasiado que hacer",
        "no puedo concentrarme",
        "no puedo enfocarme",
        "no me puedo concentrar",
        "ayúdame a organizarme",
        "help me focus",
        "estoy saturado", "estoy estresado"
    ]

    def detect(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.TRIGGERS)

    def respond(self, context: Dict[str, Any]) -> str:
        events = context.get("events", []) or []
        upcoming = events[:3]

        msg = (
            "Respira un momento conmigo… 💜\n"
            "Vamos a hacer un mini–modo Focus para que no te sientas tan cargado.\n\n"
            "✨ **PASO 1 — Una sola cosa**\n"
            "Elige SOLO una tarea para comenzar. Nada más. Una.\n\n"
        )

        if upcoming:
            msg += "Veo estas cosas próximas, dime cuál prefieres empezar:\n"
            for e in upcoming:
                msg += f"• {e.get('title')} — {e.get('when')}\n"

        msg += (
            "\n✨ **PASO 2 — Tiempo corto**\n"
            "Trabajemos solo 10 minutos. Luego vemos cómo te sientes.\n\n"
            "✨ **PASO 3 — Micro-pausa**\n"
            "Después de esos 10 min, respiramos juntos 30 segundos.\n\n"
            "Estoy aquí para guiarte. ¿Con qué te gustaría comenzar?"
        )

        return msg
