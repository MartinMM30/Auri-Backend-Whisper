# ============================================================
# ACTIONS ENGINE V4 — Compatible con AuriMind V7.7 / V7.8
# Mantiene tu estructura de intents
# ============================================================

from datetime import datetime, timedelta
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


    # =====================================================
    # UTILIDAD: FECHA ACTUAL SEGÚN CONTEXTO
    # =====================================================
    def _get_now(self, context: Dict[str, Any]) -> datetime:
        iso = context.get("current_time_iso")
        if iso:
            try:
                return datetime.fromisoformat(iso)
            except Exception:
                pass
        return datetime.utcnow()


    # =====================================================
    # UTILIDAD: ACCIÓN SEGURA
    # =====================================================
    def _make_action(self, action_type: str, payload=None):
        if action_type not in SAFE_ACTION_TYPES:
            return None
        return {"type": action_type, "payload": payload or {}}


    # =====================================================
    # CONSULTA DE AGENDA
    # =====================================================
    def _handle_consulta_agenda(self, context: Dict[str, Any]) -> str:
        events = context.get("events", []) or []
        payments = context.get("payments", []) or []

        msg = "Déjame revisar tu agenda un momento… 💜\n\n"

        if not events and not payments:
            return "Según tu agenda, no tienes pendientes importantes por ahora 💜"

        if events:
            msg += "📅 *Próximos eventos:*\n"
            for e in events[:5]:
                msg += f"• {e.get('title','Evento')} — {e.get('when','?')}\n"

        if payments:
            msg += "\n💸 *Pagos próximos:*\n"
            for p in payments[:5]:
                msg += f"• {p.get('name')} — día {p.get('day')} a las {p.get('time')}\n"

        msg += "\nSi quieres, puedo ayudarte a priorizar o crear recordatorios nuevos. 💖"
        return msg


    # =====================================================
    # CREAR RECORDATORIO
    # =====================================================
    def _handle_create_reminder(self, user_msg, context):
        extracted: ExtractedReminder = self.extractor.extract(user_msg)

        if not extracted or not extracted.title:
            return {
                "final": "¿Qué recordatorio querés crear?",
                "action": None
            }

        when = extracted.datetime or (self._get_now(context) + timedelta(hours=1))

        reminder = {
            "title": extracted.title,
            "when": when.isoformat(),
            "repeats": extracted.repeats,
            "tag": extracted.tag
        }

        self.pending_reminder = reminder

        return {
            "final": f"Perfecto, voy a crear esto: '{extracted.title}' para {when.strftime('%d/%m %H:%M')}. ¿Confirmás?",
            "action": self._make_action("create_reminder", {"pending": True})
        }


    # =====================================================
    # CONFIRMACIÓN DEL RECORDATORIO
    # =====================================================
    def _handle_confirm_reminder(self, user_msg, context):
        if not self.pending_reminder:
            return {"final": "No tengo ningún recordatorio pendiente para confirmar.", "action": None}

        reminder = self.pending_reminder
        self.pending_reminder = None

        return {
            "final": f"Perfecto, ya lo guardé 💜",
            "action": self._make_action("create_reminder", reminder)
        }


    # =====================================================
    # ELIMINAR RECORDATORIO
    # =====================================================
    def _handle_delete_reminder(self, user_msg, context):
        return {
            "final": "¿Seguro querés eliminar ese recordatorio?",
            "action": self._make_action("delete_reminder", {"query": user_msg, "confirmed": False})
        }


    # =====================================================
    # EDITAR RECORDATORIO
    # =====================================================
    def _handle_edit_reminder(self, user_msg, context):
        extracted = self.extractor.extract(user_msg)

        if not extracted or not extracted.title:
            return {"final": "¿Qué cambio querés hacer en ese recordatorio?", "action": None}

        when = extracted.datetime or self._get_now(context)

        data = {
            "title": extracted.title,
            "when": when.isoformat()
        }

        return {
            "final": f"¿Querés actualizarlo a: '{extracted.title}' para {when.strftime('%d/%m %H:%M')}?'",
            "action": self._make_action("edit_reminder", data)
        }


    # =====================================================
    # CONSULTAR RECORDATORIOS
    # =====================================================
    def _handle_query_reminders(self, context):
        events = context.get("events", [])
        if not events:
            return {"final": "No tenés recordatorios por ahora 💜", "action": None}

        msg = "Estos son tus próximos recordatorios:\n"
        for e in events[:5]:
            msg += f"• {e.get('title')} — {e.get('when')}\n"

        return {"final": msg, "action": None}


    # =====================================================
    # ENTRY POINT — versión compatible con tu sistema
    # =====================================================
    def handle(self, user_id=None, intent=None, user_msg=None, context=None, memory=None):

        if not intent:
            return {"final": None, "action": None}

        # Intent → método correcto
        if intent == "consulta_agenda":
            return {"final": self._handle_consulta_agenda(context), "action": None}

        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg, context)

        if intent == "reminder.confirm":
            return self._handle_confirm_reminder(user_msg, context)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg, context)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        if intent == "reminder.edit":
            return self._handle_edit_reminder(user_msg, context)

        return {"final": None, "action": None}
