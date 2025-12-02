# auribrain/intent_engine.py

from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class IntentEngine:

    def __init__(self, client: OpenAI):
        self.client = client

    # ================================================================
    # RULE-BASED (ROBUSTO)
    # ================================================================
    def _rule_based(self, text: str):
        if not text:
            return None

        t = text.lower().strip()

        # --- DELETE REMINDER ---
        if any(w in t for w in [
            "borra", "borrar", "elimina", "eliminar",
            "quita", "quitar", "remueve", "remover",
            "suprime", "suprimir"
        ]):
            return "reminder.remove"

        # --- QUERY REMINDERS ---
        if any(w in t for w in [
            "qué recordatorios tengo",
            "qué recordatorios hay",
            "qué tengo hoy",
            "mis recordatorios",
            "ver recordatorios",
            "lista de recordatorios",
            "dime mis recordatorios",
            "cuáles son mis recordatorios",
            "muéstrame mis recordatorios"
        ]):
            return "reminder.query"

        # --- CREATE REMINDER ---
        if any(w in t for w in [
            "recuérdame", "recuerdame",
            "pon un recordatorio",
            "crea un recordatorio",
            "crea un recordatorio para",
            "programa", "anota",
            "recordatorio para",
            "recuérdame para",
        ]):
            return "reminder.create"

        # Default
        return None

    # ================================================================
    # LLM FALLBACK
    # ================================================================
    def _llm(self, text: str):
        prompt = f"""
Clasifica este mensaje en un intent:

Opciones:
- reminder.create
- reminder.remove
- reminder.query
- conversation.general

Ejemplos:
"qué recordatorios tengo" → reminder.query  
"recuérdame tomar agua mañana" → reminder.create  
"quita el recordatorio de agua" → reminder.remove  

Mensaje: "{text}"

Responde *solo* el nombre del intent.
"""

        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": "Clasifica intenciones. Solo responde el nombre del intent."},
                    {"role": "user", "content": prompt},
                ],
            )
            return resp.output_text.strip()

        except Exception as e:
            logger.error(f"[IntentEngine] LLM error: {e}")
            return "conversation.general"

    # ================================================================
    # DECISIÓN FINAL
    # ================================================================
    def detect(self, text: str):
        rule = self._rule_based(text)
        if rule:
            return rule
        return self._llm(text)
