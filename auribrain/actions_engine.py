from datetime import datetime
from typing import Optional
from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


class ActionsEngine:

    def __init__(self):
        self.extractor = EntityExtractor()

    # ============================================================
    # ENTRADA PRINCIPAL
    # ============================================================
    def handle(self, intent: str, user_msg: str, context, memory):

        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg, memory)

        if intent == "reminder.edit":
            return self._handle_edit_reminder(user_msg)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        if intent == "reminder.confirm":
            return self._handle_confirm(memory, user_msg)

        return {"final": None, "action": None}

    # ============================================================
    # CREATE REMINDER (con soporte para confirmación)
    # ============================================================
    def _handle_create_reminder(self, user_msg: str, memory):
        now = datetime.utcnow()

        parsed = self.extractor.extract_reminder(user_msg, now=now)

        if not parsed:
            return {
                "final": "No logré entender la fecha. ¿Puedes repetirlo?",
                "action": None
            }

        # Falta fecha → guardar 'pending_reminder'
        if not parsed.datetime:
            memory.save("pending_reminder", {
                "title": parsed.title,
                "kind": parsed.kind,
            })
            return {
                "final": f"Entendí “{parsed.title}”. ¿Para qué día y hora lo programo?",
                "action": None
            }

        # Fecha encontrada → crear directamente
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
                }
            }
        }

    # ============================================================
    # EDIT REMINDER
    # ============================================================
    def _handle_edit_reminder(self, user_msg: str):
        parsed = self.extractor.extract_reminder(user_msg)

        if not parsed or not parsed.title:
            return {
                "final": "¿Qué recordatorio deseas modificar?",
                "action": None
            }

        if not parsed.datetime and parsed.repeats == "once":
            return {
                "final": f"¿A qué fecha u hora quieres mover “{parsed.title}”?",
                "action": None
            }

        return {
            "final": f"Actualizo “{parsed.title}”.",
            "action": {
                "type": "edit_reminder",
                "payload": {
                    "title": parsed.title,
                    "datetime": parsed.datetime.isoformat() if parsed.datetime else None,
                    "repeats": parsed.repeats,
                    "kind": parsed.kind,
                }
            }
        }

    # ============================================================
    # QUERY REMINDERS
    # ============================================================
    def _handle_query_reminders(self, context):
        events = context.events or []
        if not events:
            return {
                "final": "No tienes recordatorios próximos.",
                "action": {
                    "type": "open_reminders_list"
                }
            }

        lines = "\n".join(f"- {e['title']}" for e in events[:5])
        return {
            "final": f"Tienes estos recordatorios próximos:\n{lines}",
            "action": {
                "type": "open_reminders_list"
            }
        }

    # ============================================================
    # CONFIRMACIONES INTELIGENTES
    # ============================================================
    def _handle_confirm(self, memory, user_msg: str):
        pend = memory.get("pending_reminder")
        if not pend:
            return {
                "final": "¿A qué te refieres exactamente?",
                "action": None
            }

        parsed = self.extractor.extract_reminder(user_msg)
        if not parsed:
            return {
                "final": "No entendí la fecha. ¿Puedes repetirla?",
                "action": None
            }

        title = pend["title"]
        memory.delete("pending_reminder")

        return {
            "final": f"Listo, te recuerdo “{title}” el {parsed.datetime.strftime('%d/%m a las %H:%M')}.",
            "action": {
                "type": "create_reminder",
                "payload": {
                    "title": title,
                    "datetime": parsed.datetime.isoformat(),
                    "kind": pend["kind"],
                    "repeats": parsed.repeats,
                }
            }
        }

    # ============================================================
    # DELETE REMINDER (ya funciona)
    # ============================================================
    def _handle_delete_reminder(self, user_msg: str):
        # … tu versión actual está bien …
        # No la repito aquí por espacio.
        ...
