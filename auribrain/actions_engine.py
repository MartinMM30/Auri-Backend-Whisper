# auribrain/actions_engine.py

from datetime import datetime
from typing import Optional, Dict, Any

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


SAFE_ACTION_TYPES = {
    "create_reminder",
    "delete_reminder",
    "edit_reminder",
    "open_reminders_list",
}


class ActionsEngine:

    def __init__(self):
        self.extractor = EntityExtractor()

    # ==============================================================
    # UTILIDAD: OBTENER HORA REAL DEL USUARIO
    # ==============================================================
    def _get_now(self, context: dict):
        """
        Usa la hora del dispositivo que Flutter envía en current_time_iso.
        Si no existe, usa datetime.now() local del servidor.
        """
        if context and "current_time_iso" in context:
            iso = context["current_time_iso"]
            try:
                return datetime.fromisoformat(iso)
            except:
                pass

        return datetime.now()

    # ==============================================================
    # ENTRY POINT
    # ==============================================================
    def handle(self, intent: str, user_msg: str, context: Dict[str, Any], memory):

        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg, context)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg, context)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        if intent == "reminder.edit":
            return self._handle_edit_reminder(user_msg, context)

        return {"final": None, "action": None}

    # ==============================================================
    # UTILIDAD: ACCIONES SEGURAS
    # ==============================================================
    def _make_action(self, action_type: str, payload: Optional[Dict[str, Any]] = None):
        if action_type not in SAFE_ACTION_TYPES:
            return None
        return {"type": action_type, "payload": payload or {}}

    # ==============================================================
    # QUERY REMINDERS
    # ==============================================================
    def _handle_query_reminders(self, context: Dict[str, Any]):
        events = context.get("events", []) or []

        if not events:
            return {"final": "No tienes recordatorios próximos.", "action": None}

        titles = [e.get("title", "") for e in events[:5] if e.get("title")]
        if not titles:
            return {
                "final": "No pude leer bien tus recordatorios, pero sé que tienes algunos próximos.",
                "action": None,
            }

        formatted = "\n- " + "\n- ".join(titles)

        return {
            "final": f"Tienes estos recordatorios próximos:{formatted}",
            "action": self._make_action("open_reminders_list"),
        }

    # ==============================================================
    # CREATE REMINDER
    # ==============================================================
    def _handle_create_reminder(self, user_msg: str, context: dict):

        now = self._get_now(context)

        try:
            parsed = self.extractor.extract_reminder(user_msg, now=now)
        except Exception:
            parsed = None

        if not parsed:
            return {
                "final": "No logré entender la fecha del recordatorio. ¿Puedes repetirlo con día y hora?",
                "action": None,
            }

        if not parsed.datetime:
            return {
                "final": (
                    f"Entendí que deseas recordar “{parsed.title}”. "
                    "¿Para qué día y hora lo programo?"
                ),
                "action": None,
            }

        dt = parsed.datetime
        return {
            "final": (
                f"Perfecto, te recuerdo “{parsed.title}” "
                f"el {dt.strftime('%d/%m a las %H:%M')}."
            ),
            "action": self._make_action(
                "create_reminder",
                {
                    "title": parsed.title,
                    "datetime": dt.isoformat(),
                    "kind": parsed.kind,
                    "repeats": parsed.repeats,
                },
            ),
        }

    # ==============================================================
    # DELETE REMINDER (BORRADO INTELIGENTE COMPLETO)
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str, context: dict = None):

        text = user_msg.lower()
        events = []
        if context and isinstance(context, dict):
            events = context.get("events", []) or []

        # ordenar por fecha si es posible
        def sort_events(ev_list):
            try:
                return sorted(ev_list, key=lambda e: e["when"])
            except:
                return ev_list

        # ---- BORRAR TODOS ----
        if any(k in text for k in ["borra todos", "elimina todos", "quitar todos"]):
            return {
                "final": "Elimino todos tus recordatorios.",
                "action": {"type": "delete_all_reminders", "payload": {}},
            }

        # ---- BORRAR CATEGORÍA ----
        if "pago" in text or "pagos" in text:
            return {
                "final": "De acuerdo, elimino tus recordatorios de pagos.",
                "action": {"type": "delete_category", "payload": {"category": "payment"}},
            }

        if "cumple" in text or "cumpleaños" in text:
            return {
                "final": "Elimino tus recordatorios de cumpleaños.",
                "action": {"type": "delete_category", "payload": {"category": "birthday"}},
            }

        # ---- HOY / MAÑANA ----
        if "hoy" in text:
            return {
                "final": "Elimino tus recordatorios de hoy.",
                "action": {"type": "delete_by_date", "payload": {"when": "today"}},
            }

        if "mañana" in text:
            return {
                "final": "Elimino tus recordatorios de mañana.",
                "action": {"type": "delete_by_date", "payload": {"when": "tomorrow"}},
            }

        # ---- PRÓXIMO ----
        keywords_next = ["próximo", "proximo", "el que sigue", "el que viene", "siguiente"]
        if any(k in text for k in keywords_next):
            if events:
                target = sort_events(events)[0]
                return {
                    "final": f"Elimino tu próximo recordatorio: “{target['title']}”.",
                    "action": {"type": "delete_reminder", "payload": {"title": target["title"]}},
                }
            return {"final": "No encontré recordatorios próximos para borrar.", "action": None}

        # ---- MÁS RECIENTE ----
        keywords_recent = ["más reciente", "mas reciente", "más nuevo", "ultimo", "último"]
        if any(k in text for k in keywords_recent):
            if events:
                target = sort_events(events)[0]
                return {
                    "final": f"Elimino tu recordatorio más reciente: “{target['title']}”.",
                    "action": {"type": "delete_reminder", "payload": {"title": target["title"]}},
                }
            return {"final": "No encontré recordatorios recientes para borrar.", "action": None}

        # ---- TITULO NORMAL ----
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # fallback básico
        if not title:
            lowered = user_msg.lower()
            for t in ["quita ", "borra ", "elimina ", "quita el ", "elimina la "]:
                if t in lowered:
                    title = user_msg[lowered.index(t) + len(t):].strip()
                    break

        if not title:
            return {"final": "¿Qué recordatorio deseas quitar exactamente?", "action": None}

        return {
            "final": f"De acuerdo, intento eliminar “{title}”.",
            "action": {"type": "delete_reminder", "payload": {"title": title}},
        }

    # ==============================================================
    # EDIT REMINDER (INTELIGENTE)
    # ==============================================================
    def _handle_edit_reminder(self, user_msg: str, context: Dict[str, Any]):

        text = user_msg.lower()
        events = context.get("events", []) or []

        if not events:
            return {"final": "No tienes recordatorios para editar.", "action": None}

        # buscar recordatorio mencionado
        target_event = None
        for ev in events:
            title = ev.get("title", "").lower()
            if title and title in text:
                target_event = ev
                break

        if not target_event:
            return {
                "final": "¿Cuál recordatorio deseas cambiar exactamente?",
                "action": None,
            }

        old_title = target_event["title"]
        now = self._get_now(context)

        try:
            parsed = self.extractor.extract_reminder(user_msg, now=now)
        except:
            parsed = None

        if not parsed:
            return {
                "final": (
                    f"¿Qué cambio deseas hacer en “{old_title}”? "
                    "Puedes decir: “cámbialo para mañana a las 6”."
                ),
                "action": None,
            }

        new_title = parsed.title or old_title
        new_dt = parsed.datetime
        new_rep = parsed.repeats

        # solo cambio de título
        if not new_dt:
            return {
                "final": f"Perfecto, actualizo el nombre a “{new_title}”.",
                "action": self._make_action(
                    "edit_reminder",
                    {
                        "oldTitle": old_title,
                        "newTitle": new_title,
                        "datetime": target_event["when"],
                        "repeats": target_event.get("repeats", "once"),
                    },
                ),
            }

        # cambio completo
        return {
            "final": (
                f"Listo, cambio “{old_title}” por “{new_title}” para "
                f"{new_dt.strftime('%d/%m a las %H:%M')}."
            ),
            "action": self._make_action(
                "edit_reminder",
                {
                    "oldTitle": old_title,
                    "newTitle": new_title,
                    "datetime": new_dt.isoformat(),
                    "repeats": new_rep,
                },
            ),
        }
