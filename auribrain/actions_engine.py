from datetime import datetime
from typing import Optional, Dict, Any

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder

SAFE_ACTION_TYPES = {
    "create_reminder",
    "delete_reminder",
    "edit_reminder",
    "open_reminders_list",
    "delete_all_reminders",
    "delete_category",
    "delete_by_date",
}

class ActionsEngine:

    def __init__(self):
        self.extractor = EntityExtractor()
        self.pending_reminder: Optional[Dict[str, Any]] = None

    # ==============================================================
    def _get_now(self, context: Dict[str, Any]) -> datetime:
        iso = context.get("current_time_iso")
        if iso:
            try:
                return datetime.fromisoformat(iso)
            except Exception:
                pass
        return datetime.now()

    # ==============================================================
    def _make_action(self, action_type: str, payload=None):
        if action_type not in SAFE_ACTION_TYPES:
            return None
        return {"type": action_type, "payload": payload or {}}

    # ==============================================================
    # CONSULTA DE AGENDA (nuevo intent)
    # ==============================================================
    def _handle_consulta_agenda(self, context: Dict[str, Any]) -> str:
        events = context.get("events", []) or []
        payments = context.get("payments", []) or []

        msg = "Déjame revisar tu agenda un momento… 💜\n\n"

        if not events and not payments:
            return "Según tu agenda, no tienes pendientes importantes por ahora 💜"

        if events:
            msg += "📅 *Próximos eventos:*\n"
            for e in events[:5]:
                title = e.get("title", "Evento")
                when = e.get("when", "fecha desconocida")
                msg += f"• {title} — {when}\n"

        if payments:
            msg += "\n💸 *Pagos próximos:*\n"
            for p in payments[:5]:
                name = p.get("name", "Pago")
                day = p.get("day")
                time = p.get("time")
                msg += f"• {name} — día {day} a las {time}\n"

        msg += "\nSi quieres, puedo ayudarte a priorizar o crear recordatorios nuevos. 💖"
        return msg

    # ==============================================================
    # ENTRY POINT
    # ==============================================================
    def handle(self, user_id=None, intent=None, user_msg=None, context=None, memory=None):

        if intent == "consulta_agenda":
            return {
                "final": self._handle_consulta_agenda(context),
                "action": None,
            }

        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg, context)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg, context)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        if intent == "reminder.edit":
            return self._handle_edit_reminder(user_msg, context)

        if intent == "reminder.confirm":
            return self._handle_confirm_reminder(user_msg, context)

        return {"final": None, "action": None}

    # ==============================================================
    # (TODO: EL RESTO DEL ARCHIVO SIGUE IGUAL)
    # Mantengo tu implementación completa de create/delete/query/edit,
    # respondiendo a tus intents originales sin modificación.
    # ==============================================================
