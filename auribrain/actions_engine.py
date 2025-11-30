# auribrain/actions_engine.py

from datetime import datetime
from typing import Dict, Any, Optional

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


class AuriActionsEngine:
    """
    FASE 10 — Motor de acciones unificado.
    Produce:
        {
            "final": "texto para usuario",
            "action": {
                "type": "...",
                "payload": {...}
            } | None
        }
    """

    def __init__(self, extractor: EntityExtractor):
        self.extractor = extractor

    # -------------------------------------------------------------
    # API PRINCIPAL
    # -------------------------------------------------------------
    def handle(
        self,
        intent: str,
        text: str,
    ) -> Dict[str, Any]:

        if intent == "reminder.create":
            return self._handle_create(text)

        if intent == "reminder.remove":
            return self._handle_delete(text)

        # Otros intents futuros: pagos, cumpleaños, clases
        return {"final": None, "action": None}

    # -------------------------------------------------------------
    # CREAR RECORDATORIO
    # -------------------------------------------------------------
    def _handle_create(self, text: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(
            text, now=now
        )

        # No se entendió nada útil
        if not parsed:
            return {
                "final": "Intenté entender tu recordatorio, pero no logré captar fecha u hora. ¿Puedes repetirlo?",
                "action": None
            }

        # Falta fecha u hora
        if not parsed.datetime:
            return {
                "final": f"Entendí que quieres recordar “{parsed.title}”. ¿Para qué día y hora?",
                "action": None,
            }

        # Éxito: tenemos título + fecha
        dt = parsed.datetime
        dt_iso = dt.isoformat()

        fecha = dt.strftime("%d/%m a las %H:%M")
        final = f"Perfecto, te recuerdo “{parsed.title}” el {fecha}."

        action = {
            "type": "create_reminder",
            "payload": {
                "title": parsed.title,
                "datetime": dt_iso,
                "kind": parsed.kind,
                "repeats": parsed.repeats,
            }
        }

        return {"final": final, "action": action}

    # -------------------------------------------------------------
    # BORRAR RECORDATORIO
    # -------------------------------------------------------------
    def _handle_delete(self, text: str) -> Dict[str, Any]:
        parsed = self.extractor.extract_reminder(text)

        title = None

        # Caso 1: el extractor identificó un título
        if parsed and parsed.title:
            title = parsed.title

        # Caso 2: fallback manual
        else:
            lowered = text.lower()
            for k in ["quita ", "elimina ", "borra ", "cancelar "]:
                if k in lowered:
                    idx = lowered.index(k) + len(k)
                    title = text[idx:].strip()
                    break

        if not title:
            return {
                "final": "¿Cuál recordatorio quieres eliminar exactamente?",
                "action": None
            }

        final = f"Está bien, intentaré quitar el recordatorio “{title}”."

        action = {
            "type": "delete_reminder",
            "payload": {"title": title}
        }

        return {"final": final, "action": action}
