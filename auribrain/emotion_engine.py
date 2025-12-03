# auribrain/emotion_engine.py

from datetime import datetime
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

            # contexto inferido
            "context_flags": {
                "bad_weather": False,
                "user_tired": False,
                "pending_payments": 0,
                "user_happy": False,
                "relationship_discussed": False,
                "financial_worry": False,
                "user_sick": False,
                "social_pressure": False,
                "overthinking": False,
            }
        }

    # ------------------------------------------------------------------
    # DETECCIÓN AVANZADA DE EMOCIONES DEL USUARIO
    # ------------------------------------------------------------------
    def analyze_user_emotion(self, text: str) -> str:
        t = text.lower()

        # EXTREMOS NEGATIVOS
        if any(w in t for w in ["muy mal", "fatal", "horrible", "no puedo más", "ya no sé qué hacer"]):
            return "overwhelmed"

        if any(w in t for w in ["triste", "deprimido", "deprimida", "vacío", "solo", "sola", "nostalgia"]):
            return "sad"

        if any(w in t for w in ["estresado", "estresada", "ansioso", "ansiosa", "preocupado", "preocupada"]):
            return "worried"

        if any(w in t for w in ["enojado", "enojada", "molesto", "frustrado", "frustrada"]):
            return "angry"

        if any(w in t for w in ["cansado", "cansada", "agotado", "agotada", "sin energía"]):
            return "tired"

        if any(w in t for w in ["enfermo", "enferma", "resfriado", "dolor", "me duele"]):
            return "sick"

        # EMOCIONES POSITIVAS
        if any(w in t for w in ["feliz", "contento", "perfecto", "maravilloso", "excelente"]):
            return "happy"

        if any(w in t for w in ["emocionado", "emocionada", "ilusionado"]):
            return "excited"

        if any(w in t for w in ["orgulloso", "orgullosa"]):
            return "proud"

        if any(w in t for w in ["aliviado", "aliviada"]):
            return "relieved"

        # AFECTO
        if any(w in t for w in ["te quiero", "te amo", "me gustas", "eres importante"]):
            return "affectionate"

        # CONFUSIÓN, DUDA
        if any(w in t for w in ["no sé", "tengo dudas", "confuso", "confundido"]):
            return "confused"

        return "neutral"

    # ------------------------------------------------------------------
    # APLICAR EMOCIÓN INTERNA
    # ------------------------------------------------------------------
    def apply_emotion_update(self, user_emotion: str, ctx: dict):
        elapsed = (datetime.now() - self.state["last_interaction"]).total_seconds()

        if elapsed > 60:
            self.state["energy"] -= 0.03

        # CLIMA
        weather = ctx.get("weather", {})
        desc = weather.get("description", "")
        if "lluvia" in desc:
            self.state["context_flags"]["bad_weather"] = True
            self.state["mood"] = "calm"

        # PAGOS → estrés
        payments = ctx.get("events", [])
        self.state["stress"] = min(1.0, len(payments) / 20.0)

        # REGLAS SEGÚN EMOCIÓN
        if user_emotion == "sad":
            self.state["mood"] = "empathetic"
            self.state["affection"] += 0.1

        elif user_emotion == "tired":
            self.state["mood"] = "tired"
            self.state["energy"] -= 0.15

        elif user_emotion == "worried":
            self.state["mood"] = "supportive"
            self.state["stress"] += 0.1

        elif user_emotion == "angry":
            self.state["mood"] = "calming"
            self.state["affection"] += 0.05

        elif user_emotion == "happy":
            self.state["mood"] = "happy"
            self.state["energy"] += 0.15

        elif user_emotion == "excited":
            self.state["mood"] = "excited"
            self.state["energy"] += 0.2

        elif user_emotion == "affectionate":
            self.state["mood"] = "affectionate"
            self.state["affection"] += 0.25

        elif user_emotion == "proud":
            self.state["mood"] = "celebratory"

        elif user_emotion == "overwhelmed":
            self.state["mood"] = "protective"
            self.state["affection"] += 0.1
            self.state["stress"] += 0.2

        elif user_emotion == "confused":
            self.state["mood"] = "guiding"

        elif user_emotion == "sick":
            self.state["mood"] = "concerned"
            self.state["affection"] += 0.05

        elif user_emotion == "relieved":
            self.state["mood"] = "calm_happy"

        self.state["last_user_emotion"] = user_emotion
        self.state["last_interaction"] = datetime.now()

        # clamp
        for k in ["energy", "stress", "affection"]:
            self.state[k] = max(0.0, min(1.0, self.state[k]))

    # ------------------------------------------------------------------
    # EMOCIÓN FINAL DEL SLIME – mucho más rica
    # ------------------------------------------------------------------
    def resolve_overall_state(self):
        m = self.state["mood"]
        e = self.state["energy"]
        s = self.state["stress"]
        a = self.state["affection"]

        # PRIORIDAD ALTA
        if m == "protective":
            return "protective"

        if m == "concerned":
            return "concerned"

        if m == "calming":
            return "calming"

        if m == "guiding":
            return "guiding"

        if m == "celebratory":
            return "celebratory"

        if m == "excited":
            return "excited"

        # AFECTO Y EMPATÍA
        if m == "affectionate" or a > 0.7:
            return "affectionate"

        if m == "empathetic":
            return "empathetic"

        # FELICIDAD
        if m == "happy" and e > 0.6:
            return "happy"

        # ESTRÉS
        if s > 0.6:
            return "stressed"

        # CANSANCIO
        if e < 0.3:
            return "tired"

        # ESTADO BASE
        return "neutral"
