import json
import logging
from openai import OpenAI

logger = logging.getLogger("uvicorn.error")

class IntentEngine:
    def __init__(self, client: OpenAI = None):
        self.client = client or OpenAI()

    # ================================================================
    # SAFE JSON
    # ================================================================
    def _safe_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except Exception:
            logger.error("[IntentEngine] JSON inválido recibido: %s", text)
            return {}

    # ================================================================
    # REGLAS PRINCIPALES (rápido + barato)
    # ================================================================
    def _rule_based(self, t):
        t = t.lower()

        # ------------------------------
        # 🔵 REMINDER.QUERY
        # ------------------------------
        if any(k in t for k in [
            "mis recordatorios",
            "qué recordatorios tengo",
            "que recordatorios tengo",
            "lista de recordatorios",
            "muéstrame mis recordatorios",
            "mostrar recordatorios",
            "ver recordatorios",
            "recordatorios de hoy",
            "recordatorios pendientes",
        ]):
            return "reminder.query"

        # ------------------------------
        # 🔵 REMINDER.CREATE
        # ------------------------------
        if any(k in t for k in [
            "recorda ", "recuérdame", "recuerdame",
            "pon un recordatorio",
            "crea un recordatorio",
            "agrega un recordatorio",
            "anota que",
            "recuerda que",
            "haz un recordatorio",
        ]):
            return "reminder.create"

        # ------------------------------
        # 🔵 REMINDER.DELETE
        # ------------------------------
        if "quita" in t and "recordatorio" in t:
            return "reminder.remove"

        # ------------------------------
        # 🔵 WEATHER
        # ------------------------------
        if any(k in t for k in ["clima", "temperatura", "tiempo"]):
            return "weather.query"

        # ------------------------------
        # 🔵 OUTFIT
        # ------------------------------
        if any(k in t for k in ["outfit", "qué me pongo", "que me pongo", "ropa"]):
            return "outfit.suggest"

        # ------------------------------
        # 🔵 USER STATE
        # ------------------------------
        if any(k in t for k in ["cómo estoy", "como estoy", "cómo me ves", "como me ves"]):
            return "user.state"

        # ------------------------------
        # 🔵 CONFIG AURI
        # ------------------------------
        if any(k in t for k in ["personalidad", "tu voz"]):
            return "auri.config"

        # ------------------------------
        # 🔵 EMOTION SUPPORT
        # ------------------------------
        if any(k in t for k in ["estoy triste", "estresado", "ansioso"]):
            return "emotion.support"

        # ------------------------------
        # 🔵 GREETING
        # ------------------------------
        if any(k in t for k in ["hola", "buenos días", "buenas tardes", "buenas noches"]):
            return "smalltalk.greeting"

        # ------------------------------
        # 🔵 JOKE
        # ------------------------------
        if any(k in t for k in ["chiste", "divertido"]):
            return "fun.joke"

        return None

    # ================================================================
    # LLM fallback
    # ================================================================
    def _llm(self, text):
        prompt = f"""
Clasifica el siguiente mensaje EN SOLO UNO de estos intents:

- reminder.create
- reminder.remove
- reminder.query
- weather.query
- outfit.suggest
- knowledge.query
- smalltalk.greeting
- fun.joke
- user.state
- emotion.support
- auri.config
- conversation.general

Ejemplo:
"qué recordatorios tengo" → reminder.query
"recuérdame tomar agua mañana" → reminder.create
"quita el recordatorio de agua" → reminder.remove

Mensaje:
"{text}"

Responde SOLO el nombre del intent.
"""

        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": "Eres un clasificador experto. Solo responde un intent."},
                    {"role": "user", "content": prompt},
                ]
            )
            return resp.output_text.strip()
        except Exception as e:
            logger.error(f"[IntentEngine] LLM error: {e}")
            return "conversation.general"

    # ================================================================
    # ENTRADA PRINCIPAL
    # ================================================================
    def detect(self, text):
        rule = self._rule_based(text)
        if rule:
            return rule

        return self._llm(text)
