import json
import logging
from openai import OpenAI

logger = logging.getLogger("uvicorn.error")

class IntentEngine:
    def __init__(self, client: OpenAI = None):
        # Usa el cliente recibido o crea uno propio
        self.client = client or OpenAI()

    # ================================================================
    # SAFE JSON
    # ================================================================
    def _safe_json(self, text: str) -> dict:
        """
        Intenta decodificar JSON estricto.
        Si falla, devuelve {} y marca error.
        """
        try:
            return json.loads(text)
        except Exception:
            logger.error("[IntentEngine] JSON inválido recibido: %s", text)
            return {}

    # ================================================================
    # RULE-BASED DETECTION (rápido y barato)
    # ================================================================
    def _rule_based(self, t):
        t = t.lower()

        # CREATE REMINDER
        if any(k in t for k in [
            "recorda", "recuérdame", "recuerdame", "pon un recordatorio",
            "crea un recordatorio", "agrega un recordatorio",
            "anota que", "recuerda que", "haz un recordatorio",
        ]):
            return "reminder.create"

        # DELETE REMINDER
        if "quita" in t and "recordatorio" in t:
            return "reminder.remove"

        # WEATHER
        if any(k in t for k in ["clima", "temperatura", "tiempo"]):
            return "weather.query"

        # OUTFIT
        if any(k in t for k in ["outfit", "qué me pongo", "que me pongo", "ropa"]):
            return "outfit.suggest"

        # USER STATE
        if any(k in t for k in ["cómo estoy", "como estoy", "cómo me ves", "como me ves"]):
            return "user.state"

        # AURI CONFIG
        if any(k in t for k in ["personalidad", "tu voz"]):
            return "auri.config"

        # EMOTION SUPPORT
        if any(k in t for k in ["estoy triste", "estresado"]):
            return "emotion.support"

        # GREETINGS
        if any(k in t for k in ["hola", "buenos días", "buenas tardes", "buenas noches"]):
            return "smalltalk.greeting"

        # JOKE
        if any(k in t for k in ["chiste", "divertido"]):
            return "fun.joke"

        return None

    # ================================================================
    # LLM fallback
    # ================================================================
    def _llm(self, text):
        prompt = f"""
Clasifica este mensaje en un solo intent válido:
- reminder.create
- reminder.remove
- weather.query
- outfit.suggest
- knowledge.query
- smalltalk.greeting
- fun.joke
- user.state
- emotion.support
- auri.config
- conversation.general

Mensaje: "{text}"

Responde SOLO con uno de los intents de la lista.
"""

        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": "Eres un clasificador experto."},
                    {"role": "user", "content": prompt},
                ]
            )
            return resp.output_text.strip()
        except Exception as e:
            logger.error(f"[IntentEngine] LLM error: {e}")
            return "conversation.general"

    # ================================================================
    # PUBLIC ENTRYPOINT
    # ================================================================
    def detect(self, text):
        rule = self._rule_based(text)
        if rule:
            return rule

        return self._llm(text)
