# auribrain/intent_engine.py

from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class IntentEngine:

    def __init__(self, client: OpenAI):
        self.client = client

    # ================================================================
    # RULE-BASED (rápido)
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

        # --- EDIT REMINDER ---
        if any(w in t for w in [
            "cambia", "cambiar", "modifica", "modificar",
            "muévelo", "muevelo", "mover",
            "adelanta", "atrasa", "ajusta", "edita"
        ]):
            return "reminder.edit"

        # --- QUERY REMINDERS ---
        if any(w in t for w in [
            "qué recordatorios tengo",
            "que recordatorios tengo",
            "mis recordatorios",
            "ver recordatorios",
            "lista de recordatorios"
        ]):
            return "reminder.query"

        # --- CONFIRM REMINDER ---
        if any(phrase in t for phrase in [
            "sí, está bien",
            "si, esta bien",
            "sí está bien",
            "si esta bien",
            "ok, crea",
            "ok crea",
            "está bien así",
            "esta bien asi",
            "confirma",
            "confirmalo",
            "confirmar",
            "dale, hazlo",
            "sí, hazlo",
            "si, hazlo"
        ]):
            return "reminder.confirm"

        # --- CREATE REMINDER ---
        if any(w in t for w in [
            "recordatorio",
            "recuérdame", "recuerdame",
            "crea", "crear",
            "programa", "agenda esto",
            "anota", "agéndame", "agendame"
        ]):
            return "reminder.create"

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
- reminder.edit
- reminder.confirm
- conversation.general

Ejemplos:
"qué recordatorios tengo" → reminder.query
"recuérdame tomar agua mañana" → reminder.create
"quita el recordatorio de agua" → reminder.remove
"cambia el recordatorio de luz para mañana" → reminder.edit
"sí, está bien mañana a las 5" → reminder.confirm

Mensaje:
"{text}"

Responde SOLO el nombre del intent.
"""

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un clasificador experto. Solo responde un intent."
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"[IntentEngine] LLM error: {e}")
            return "conversation.general"

    # ================================================================
    # ENTRADA PRINCIPAL
    # ================================================================
    def detect(self, text: str):
        # 1) Primero reglas (rápido)
        rule = self._rule_based(text)
        if rule:
            return rule

        # 2) Fallback LLM
        return self._llm(text)
