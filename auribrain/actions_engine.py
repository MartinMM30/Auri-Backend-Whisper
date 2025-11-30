# auribrain/actions_engine.py

from datetime import datetime
from typing import Any, Dict, Optional
from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


class ActionsEngine:
    """
    Procesa intents y devuelve:
      - final: texto para el usuario
      - action: instrucción para Flutter
    """

    def __init__(self):
        self.extractor = EntityExtractor()

    # Punto principal
    def handle(self, intent: str, user_msg: str, context, memory):
        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg)

        return {"final": None, "action": None}

    # ---------------- CREATE ----------------
    def _handle_create_reminder(self, user_msg: str):
        now = datetime.utcnow()
        parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(user_msg, now=now)

        if not parsed:
            return {
                "final": "No logré entender la fecha del recordatorio. ¿Puedes repetirlo con fecha y hora?",
                "action": None
            }

        if not parsed.datetime:
            return {
                "final": f"Entendí que deseas recordar “{parsed.title}”. ¿Me dices para cuándo?",
                "action": None
            }

        dt = parsed.datetime
        dt_iso = dt.isoformat()

        final_text = f"Perfecto, te recuerdo “{parsed.title}” el {dt.strftime('%d/%m a las %H:%M')}."

        return {
            "final": final_text,
            "action": {
                "type": "create_reminder",
                "payload": {
                    "title": parsed.title,
                    "datetime": dt_iso,
                    "kind": parsed.kind,
                    "repeats": parsed.repeats,
                },
            },
        }

    # ---------------- DELETE ----------------
    def _handle_delete_reminder(self, user_msg: str):
        parsed = self.extractor.extract_reminder(user_msg)

        title = parsed.title if parsed and parsed.title else None

        if not title:
            lowered = user_msg.lower()
            for key in ["quita ", "elimina ", "borra "]:
                if key in lowered:
                    idx = lowered.index(key) + len(key)
                    title = user_msg[idx:].strip()
                    break

        if not title:
            return {
                "final": "¿Qué recordatorio deseas quitar?",
                "action": None
            }

        return {
            "final": f"De acuerdo, intento eliminar “{title}”.",
            "action": {
                "type": "delete_reminder",
                "payload": {"title": title}
            }
        }
