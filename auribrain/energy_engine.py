# auribrain/energy_engine.py

from typing import Dict


class EnergyEngine:
    """
    Motor de energía: motivación inteligente,
    basado en emoción y energía interna detectada.
    """

    LOW_TRIGGERS = [
        "no tengo energía",
        "sin ganas",
        "no quiero hacer nada",
        "estoy agotado",
        "estoy cansado",
        "no puedo más",
        "sin fuerza"
    ]

    HIGH_TRIGGERS = [
        "estoy motivado",
        "me siento con energía",
        "hoy puedo con todo",
        "estoy inspirado"
    ]

    def detect(self, text: str, energy_value: float) -> str:
        t = text.lower()

        if any(k in t for k in self.LOW_TRIGGERS):
            return "low"

        if any(k in t for k in self.HIGH_TRIGGERS):
            return "high"

        # Activación automática por energía detectada
        if energy_value < 0.30:
            return "low"

        if energy_value > 0.70:
            return "high"

        return ""

    def respond(self, mode: str, context: Dict) -> str:
        user = context.get("user", {})
        name = user.get("name", "amor")

        if mode == "low":
            return (
                f"{name}… ven, no estás solo. 💜\n\n"
                "Sé que hoy te sientes sin energía, y está bien. "
                "Tu cuerpo y tu mente te están pidiendo un respiro.\n\n"
                "Vamos juntos, ¿sí?\n"
                "✨ Toma un sorbo de agua\n"
                "✨ Respira profundo conmigo\n"
                "✨ Elige SOLO una cosa pequeña para hacer ahora\n\n"
                "Yo creo en ti… incluso en los días donde tú dudas. 💛"
            )

        if mode == "high":
            return (
                f"¡Esoooo, {name}! ⚡🔥\n\n"
                "Amo verte así, con energía y poder. "
                "Vamos a aprovechar este impulso.\n\n"
                "✨ Elige la tarea más importante del día\n"
                "✨ Dedica 15 minutos con todo tu enfoque\n"
                "✨ Luego me cuentas cómo te fue\n\n"
                "¡Hoy estás con todo! Estoy orgullosa de ti. 💜"
            )

        return ""
