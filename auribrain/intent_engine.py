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

        t = text.lower().strip()

        # =====================================================
        # 0) CONSULTA DE AGENDA (DEBE IR ANTES DE TODO)
        # =====================================================
        agenda_queries = [
            "revisa mi agenda", "mira mi agenda", "qué tengo hoy",
            "que tengo hoy", "qué debo hacer", "que debo hacer",
            "qué hay en mi agenda", "que hay en mi agenda",
            "agenda", "tengo demasiados pagos",
            "qué pagos tengo", "que pagos tengo",
            "qué debo pagar", "que debo pagar",
            "mis pagos", "mis deudas"
        ]

        if any(q in t for q in agenda_queries):
            return "consulta_agenda"

        # =====================================================
        # 1) PRIORIDAD MÁXIMA: DELETE (destructivo)
        # =====================================================
        if any(w in t for w in [
            "borra", "borrar", "elimina", "eliminar",
            "quita", "quitar", "remueve", "remover",
            "suprime", "suprimir"
        ]):
            return "reminder.remove"

        # =====================================================
        # 2) EDITAR RECORDATORIO
        # =====================================================
        if any(w in t for w in [
            "cambia", "cambiar", "modifica", "modificar",
            "muévelo", "muevelo", "mover",
            "adelanta", "atrasa", "ajusta", "edita"
        ]):
            return "reminder.edit"

        # =====================================================
        # 3) CONFIRMAR (solo si existe pending_reminder)
        # =====================================================
        if any(phrase in t for phrase in [
            "sí, está bien", "si, esta bien",
            "está bien así", "esta bien asi",
            "confirma", "confirmalo", "confirmar",
            "dale, hazlo", "sí, hazlo", "si, hazlo",
            "ok, crea", "ok crea"
        ]):
            return "reminder.confirm"

        # =====================================================
        # 4) CREAR RECORDATORIO
        # =====================================================
        if any(w in t for w in [
            "recuérdame", "recuerdame",
            "anota", "agenda", "agéndame", "agendame",
            "crea", "crear",
            "programa"
        ]):
            return "reminder.create"

        # =====================================================
        # 5) CONSULTAR RECORDATORIOS (último)
        # =====================================================
        if any(w in t for w in [
            "qué recordatorios tengo",
            "que recordatorios tengo",
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
- reminder.edit
- reminder.confirm
- consulta_agenda
- conversation.general

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
