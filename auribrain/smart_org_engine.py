# auribrain/smart_org_engine.py

from datetime import datetime
from typing import Dict, Any, List


class SmartOrganizationEngine:
    """
    Analiza:
    - Estado emocional del usuario
    - Eventos, pagos, carga diaria
    - Hora del día

    Produce:
    - Consejos prácticos
    - Priorización automática
    - Microacciones (respirar, pausa, grounding, celebrar)
    """

    def analyze(self, emotion: str, ctx: Dict[str, Any]) -> str:
        events = ctx.get("events", []) or []
        payments = ctx.get("payments", []) or []
        classes = ctx.get("classes", []) or []
        exams = ctx.get("exams", []) or []

        # ============================================================
        # 1) MICRO–ACCIONES EMOCIONALES
        # ============================================================
        if emotion in ["worried", "anxious", "stressed"]:
            return (
                "Respiremos juntos un momento… 💜\n"
                "Inhala profundo… 3 segundos… ahora exhala suavemente.\n\n"
                "Entiendo que te sientas así. Vamos a revisar tus pendientes:"
                f"\n- Pagos próximos: {len(payments)}"
                f"\n- Eventos próximos: {len(events)}\n\n"
                "Si quieres, puedo ayudarte a priorizar o dividirlos en pasos pequeños."
            )

        if emotion == "sad":
            return (
                "Siento que estés pasando por un momento así… 💜\n"
                "No estás solo. Podemos ir despacio.\n\n"
                "Déjame revisar tu día y ver cómo puedo ayudarte suavemente.\n"
            )

        if emotion == "tired":
            return (
                "Has estado esforzándote muchísimo… 💜\n"
                "Creo que tu cuerpo está pidiendo una pausa.\n"
                "Te recomiendo descansar al menos 5 minutos.\n"
                "¿Quieres que reorganice tu agenda para que tengas más aire?"
            )

        if emotion == "angry":
            return (
                "Entiendo esa sensación, de verdad… 😔\n"
                "Antes de tomar decisiones apresuradas, hagamos grounding:\n"
                "• Siente tus pies en el suelo\n"
                "• Respira lento tres veces\n\n"
                "Si deseas, reviso tu agenda para ayudarte a deshacerte de lo que te está saturando."
            )

        if emotion in ["happy", "affectionate"]:
            # Celebración + repaso
            msg = (
                "¡Awww, me hace TAN feliz verte así! 💖✨\n"
                "Celebremos tus logros un momento.\n\n"
                "Mira, para aprovechar tu energía, esto es lo que viene:\n"
            )
            for e in events[:3]:
                msg += f"• {e.get('title')} — {e.get('when')}\n"
            return msg + "\n¿Quieres avanzar algo mientras te sientes motivado? 💜"

        # Emotion neutral = default smart insights
        return self._neutral_insights(ctx)

    # ============================================================
    # Modo neutral → insight general inteligente
    # ============================================================
    def _neutral_insights(self, ctx: Dict[str, Any]) -> str:
        events = ctx.get("events", []) or []
        payments = ctx.get("payments", []) or []

        msg = "Aquí tienes un resumen rápido inteligente del día 💜\n\n"

        if events:
            msg += "📅 Próximos eventos:\n"
            for e in events[:5]:
                msg += f"• {e.get('title')} — {e.get('when')}\n"

        if payments:
            msg += "\n💸 Pagos próximos:\n"
            for p in payments[:5]:
                msg += f"• {p.get('name')} — día {p.get('day')} a las {p.get('time')}\n"

        msg += "\nSi quieres, puedo ayudarte a priorizar o dividir tareas en pasos más pequeños."
        return msg
