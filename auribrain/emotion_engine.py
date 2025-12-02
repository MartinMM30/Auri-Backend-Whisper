# auribrain/emotion_engine.py

from datetime import datetime, timedelta
import math

class EmotionEngine:

    def __init__(self):
        self.state = {
            "mood": "neutral",
            "energy": 0.7,
            "stress": 0.1,
            "affection": 0.5,
            "confidence": 0.5,
            "focus": 0.5,
            "last_user_emotion": "neutral",
            "last_interaction": datetime.now(),
            "context_flags": {
                "bad_weather": False,
                "user_tired": False,
                "pending_payments": 0,
                "user_happy": False,
            }
        }

    # ------------------------------------------------------------------
    # ANALIZA EL MENSAJE DEL USUARIO (emocional)
    # ------------------------------------------------------------------
    def analyze_user_emotion(self, text: str) -> str:
        text_l = text.lower()

        if any(w in text_l for w in ["triste", "mal", "cansado", "cansada", "agotado", "agotada", "estresado"]):
            return "sad"

        if any(w in text_l for w in ["feliz", "contento", "genial", "perfecto", "emocionado"]):
            return "happy"

        if any(w in text_l for w in ["te quiero", "me gustas", "eres importante"]):
            return "affectionate"

        if any(w in text_l for w in ["preocupado", "ansioso", "miedo"]):
            return "worried"

        return "neutral"

    # ------------------------------------------------------------------
    # ACTUALIZA EL ESTADO EMOCIONAL INTERNO
    # ------------------------------------------------------------------
    def apply_emotion_update(self, user_emotion: str, ctx: dict):
        # tiempo desde última interacción (para bajar energía)
        elapsed = (datetime.now() - self.state["last_interaction"]).total_seconds()
        if elapsed > 60:
            self.state["energy"] = max(0, self.state["energy"] - 0.05)

        # aplicar impacto del clima
        weather = ctx.get("weather", {})
        if "lluvia" in weather.get("description", ""):
            self.state["mood"] = "calm"

        # pagos → stress
        payments = ctx.get("payments", [])
        stress_fact = len(payments) / 10.0
        self.state["stress"] = min(1.0, stress_fact)

        # emoción del usuario influye directamente
        if user_emotion == "sad":
            self.state["mood"] = "empathetic"
            self.state["affection"] += 0.1

        elif user_emotion == "happy":
            self.state["mood"] = "happy"
            self.state["energy"] += 0.1

        elif user_emotion == "affectionate":
            self.state["mood"] = "affectionate"
            self.state["affection"] += 0.2

        elif user_emotion == "worried":
            self.state["mood"] = "supportive"
            self.state["stress"] += 0.1

        self.state["last_user_emotion"] = user_emotion
        self.state["last_interaction"] = datetime.now()

        # clamp valores
        self.state["energy"] = max(0, min(1, self.state["energy"]))
        self.state["stress"] = max(0, min(1, self.state["stress"]))
        self.state["affection"] = max(0, min(1, self.state["affection"]))

    # ------------------------------------------------------------------
    # DEVUELVE EMOCIÓN FINAL PARA SLIME, RESPUESTAS Y VOZ
    # ------------------------------------------------------------------
    def resolve_overall_state(self):
        m = self.state["mood"]
        s = self.state["stress"]
        e = self.state["energy"]
        a = self.state["affection"]

        if m == "affectionate" or a > 0.7:
            return "affectionate"

        if m == "happy" and e > 0.6:
            return "happy"

        if s > 0.6:
            return "stressed"

        if m in ["empathetic", "supportive"]:
            return "empathetic"

        if e < 0.3:
            return "tired"

        return "neutral"
