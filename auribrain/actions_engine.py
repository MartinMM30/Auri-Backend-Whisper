from datetime import datetime
from typing import Optional
from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


class ActionsEngine:
    """
    Procesa intents y devuelve:
      - final: texto para el usuario
      - action: instrucción para Flutter
    """

    def __init__(self):
        self.extractor = EntityExtractor()

    # ==============================================================  
    # ENTRY POINT  
    # ==============================================================  
    def handle(self, intent: str, user_msg: str, context: dict, memory):
        
        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        if intent == "reminder.edit":
            return self._handle_edit_reminder(user_msg, context)

        return {"final": None, "action": None}

    # ==============================================================  
    # QUERY REMINDERS  
    # ==============================================================  
    def _handle_query_reminders(self, context: dict):

        events = context.get("events", [])  # FIX: dict-access

        if not events:
            return {
                "final": "No tienes recordatorios próximos.",
                "action": None
            }

        # Tomamos solo próximos 5
        titles = [e["title"] for e in events[:5]]

        formatted = "\n- " + "\n- ".join(titles)

        return {
            "final": f"Tienes estos recordatorios próximos:{formatted}",
            "action": {"type": "open_reminders_list"}
        }

    # ==============================================================  
    # CREATE REMINDER  
    # ==============================================================  
    def _handle_create_reminder(self, user_msg: str):

        now = datetime.utcnow()

        try:
            parsed: Optional[ExtractedReminder] = \
                self.extractor.extract_reminder(user_msg, now=now)
        except Exception:
            parsed = None

        if not parsed:
            return {
                "final": "No logré entender la fecha del recordatorio. ¿Puedes repetirlo con fecha y hora?",
                "action": None
            }

        if not parsed.datetime:
            return {
                "final": f"Entendí que deseas recordar “{parsed.title}”. ¿Para qué día y hora lo programo?",
                "action": None
            }

        dt = parsed.datetime
        dt_iso = dt.isoformat()

        return {
            "final": f"Perfecto, te recuerdo “{parsed.title}” el {dt.strftime('%d/%m a las %H:%M')}.",
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

    # ==============================================================  
    # DELETE REMINDER  
    # ==============================================================  
    def _handle_delete_reminder(self, user_msg: str):

        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # FALLBACKS…
        if not title:
            lowered = user_msg.lower()
            triggers = [
                "quita ", "borra ", "elimina ",
                "quiero quitar ", "quiero borrar ", "quiero eliminar ",
                "quita el ", "quita la ", "elimina el ", "elimina la "
            ]
            for t in triggers:
                if t in lowered:
                    idx = lowered.index(t) + len(t)
                    title = user_msg[idx:].strip()
                    break

        if not title:
            return {
                "final": "¿Qué recordatorio deseas quitar?",
                "action": None
            }

        clean_title = title.strip()

        return {
            "final": f"De acuerdo, intento eliminar “{clean_title}”.",
            "action": {
                "type": "delete_reminder",
                "payload": {"title": clean_title}
            },
        }

    # ==============================================================  
    # EDIT REMINDER  
    # ==============================================================  
    def _handle_edit_reminder(self, user_msg: str, context: dict):
        """
        FUTURO:
        “Cambia el recordatorio de estudiar a las 6”
        “Muévelo para mañana”
        """

        # TEMPORAL: placeholder para que no crashee
        return {
            "final": "¿Qué cambio deseas hacer exactamente en el recordatorio?",
            "action": None
        }
