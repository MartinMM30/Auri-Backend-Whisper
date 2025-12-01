# auribrain/intent_engine.py

from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class IntentEngine:

    def __init__(self, client: OpenAI):
        self.client = client

    # ================================================================
    # RULE-BASED (robusto y ultra rápido)
    # ================================================================
    def _rule_based(self, text: str):
        if not text:
            return None

        t = text.lower()

        # --- DELETE REMINDER ---
        if any(w in t for w in [
            "borra", "borrar", "elimina", "eliminar",
            "quita", "quitar", "remueve", "remover",
            "suprime", "suprimir"
        ]):
            return "reminder.remove"

        # --- CREATE REMINDER ---
        if any(w in t for w in [
            "recordatorio", "recuérdame", "recuerdame",
            "crea", "crear", "programa", "agenda esto",
            "anota", "agéndame", "agendame"
        ]):
            return "reminder.create"

        # --- QUERY REMINDERS ---
        if any(w in t for w in [
            "qué recordatorios tengo",
            "mis recordatorios",
            "ver recordatorios",
            "lista de recordatorios"
        ]):
            return "reminder.query"

        return None

    # ================================================================
    # LLM FALLBACK
    # ================================================================
    def _llm(self, text: str):
        prompt = f"""
Clasifica este mensaje en un intent.

Opciones:
- reminder.create
- reminder.remove
- reminder.query
- conversation.general

Ejemplos:
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
                    {"role": "user", "content": prompt}
                ]
            )
            return resp.output_text.strip()
        except Exception as e:
            logger.error(f"[IntentEngine] LLM error: {e}")
            return "conversation.general"

    # ================================================================
    # ENTRADA PRINCIPAL
    # ================================================================
    def detect(self, text: str):
        # 1) Primero reglas (rápido y 100% confiable)
        rule = self._rule_based(text)
        if rule:
            return rule

        # 2) Fallback al LLM
        return self._llm(text)
