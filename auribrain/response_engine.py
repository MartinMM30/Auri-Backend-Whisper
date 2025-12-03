# auribrain/response_engine.py

from auribrain.smart_org_engine import SmartOrganizationEngine
from auribrain.crisis_engine import CrisisEngine
from auribrain.focus_engine import FocusEngine


class ResponseEngine:

    def __init__(self):
        self.org = SmartOrganizationEngine()
        self.crisis = CrisisEngine()
        self.focus = FocusEngine()

    def build(
        self,
        intent,
        style,
        context,
        memory,
        user_msg,
        raw_answer,
        emotion_state,
        emotion_snapshot
    ):
        txt = user_msg.lower()

        # ============================================================
        # 1) CRISIS EMOCIONAL (máxima prioridad)
        # ============================================================
        if self.crisis.detect(txt):
            return self.crisis.respond(context)

        # ============================================================
        # 2) MODO FOCUS (enfoque)
        # ============================================================
        if self.focus.detect(txt) or emotion_state in ["stressed", "overwhelmed"]:
            return self.focus.respond(context)

        # ============================================================
        # 3) MICRO–RESPUESTAS POR EMOCIÓN
        # ============================================================
        if emotion_state in [
            "worried", "stressed", "sad", "angry",
            "tired", "happy", "affectionate"
        ]:
            emotional_help = self.org.analyze(emotion_state, context)
            return emotional_help + "\n\n" + raw_answer

        # ============================================================
        # 4) RESPUESTAS CORTAS / QA simples
        # ============================================================
        user = context.get("user", {})
        weather = context.get("weather", {})

        if "mi nombre" in txt:
            return f"Te llamas {user.get('name', 'amor')} 💜"

        if "mi ciudad" in txt or "donde vivo" in txt:
            city = user.get("city")
            return f"Vives en {city} 💜" if city else "No tengo tu ciudad guardada."

        if "clima" in txt:
            if not weather.get("temp"):
                return "No tengo el clima aún, intenta sincronizarlo 💜"
            return f"En {user.get('city', 'tu ciudad')} hay {weather['temp']}°C y {weather['description']}."

        # ============================================================
        # 5) FALLBACK — respuesta emocional generada por LLM
        # ============================================================
        return raw_answer
