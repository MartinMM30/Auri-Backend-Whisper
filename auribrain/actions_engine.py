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
    # ENTRY POINT
    # ==============================================================
    def handle(self, intent: str, user_msg: str, context: Dict[str, Any], memory):

        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg)

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
    def _handle_create_reminder(self, user_msg: str):
        now = datetime.utcnow()

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
                "final": f"Entendí que deseas recordar “{parsed.title}”. ¿Para qué día y hora lo programo?",
                "action": None,
            }

        dt = parsed.datetime
        return {
            "final": f"Perfecto, te recuerdo “{parsed.title}” el {dt.strftime('%d/%m a las %H:%M')}.",
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
    # DELETE REMINDER  (TU SISTEMA COMPLETO)
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str, context: dict = None):

        text = user_msg.lower()
        events = []
        if context and isinstance(context, dict):
            events = context.get("events", []) or []

        # ===========================================================
        # UTIL: ordenar por fecha
        # ===========================================================
        def sort_events(ev_list):
            try:
                return sorted(ev_list, key=lambda e: e["when"])
            except:
                return ev_list

        # ===========================================================
        # 1) BORRAR TODOS
        # ===========================================================
        if any(k in text for k in ["borra todos", "elimina todos", "quitar todos"]):
            return {
                "final": "Elimino todos tus recordatorios.",
                "action": {
                    "type": "delete_all_reminders",
                    "payload": {}
                },
            }

        # ===========================================================
        # 2) BORRAR POR CATEGORÍA
        # ===========================================================
        if "pago" in text or "pagos" in text:
            return {
                "final": "De acuerdo, elimino tus recordatorios de pagos.",
                "action": {
                    "type": "delete_category",
                    "payload": {"category": "payment"},
                },
            }

        if "cumple" in text or "cumpleaños" in text:
            return {
                "final": "Elimino tus recordatorios de cumpleaños.",
                "action": {
                    "type": "delete_category",
                    "payload": {"category": "birthday"},
                },
            }

        # ===========================================================
        # 3) BORRAR RECORDATORIOS DE HOY / MAÑANA
        # ===========================================================
        if "de hoy" in text or "hoy" in text:
            return {
                "final": "Elimino tus recordatorios de hoy.",
                "action": {
                    "type": "delete_by_date",
                    "payload": {"when": "today"},
                },
            }

        if "de mañana" in text or "mañana" in text:
            return {
                "final": "Elimino tus recordatorios de mañana.",
                "action": {
                    "type": "delete_by_date",
                    "payload": {"when": "tomorrow"},
                },
            }

        # ===========================================================
        # 4) BORRAR PRÓXIMO RECORDATORIO
        # ===========================================================
        keywords_next = [
            "próximo", "proximo", "el que sigue", "el que viene", "siguiente"
        ]
        if any(k in text for k in keywords_next):
            if events:
                sorted_events = sort_events(events)
                target = sorted_events[0]
                return {
                    "final": f"Elimino tu próximo recordatorio: “{target['title']}”.",
                    "action": {
                        "type": "delete_reminder",
                        "payload": {"title": target["title"]}
                    },
                }
            return {"final": "No encontré recordatorios próximos para borrar.", "action": None}

        # ===========================================================
        # 5) BORRAR MÁS RECIENTE (el mismo que 'próximo', pero semántico)
        # ===========================================================
        keywords_recent = [
            "más reciente", "mas reciente", "más nuevo", "ultimo", "último",
            "el más reciente", "el mas reciente"
        ]
        if any(k in text for k in keywords_recent):
            if events:
                sorted_events = sort_events(events)
                target = sorted_events[0]
                return {
                    "final": f"Elimino tu recordatorio más reciente: “{target['title']}”.",
                    "action": {
                        "type": "delete_reminder",
                        "payload": {"title": target["title"]},
                    },
                }
            return {"final": "No encontré recordatorios recientes para borrar.", "action": None}

        # ===========================================================
        # 6) BORRAR POR TÍTULO NORMAL (extractor + fallback)
        # ===========================================================
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # Fallback por texto después del verbo
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

        # Fallback semántico ligero (pago, agua, luz…)
        if not title:
            keywords = [
                "agua", "luz", "internet", "teléfono", "telefono",
                "renta", "alquiler", "gato", "perro", "tarea",
                "examen", "pago", "recordatorio"
            ]
            l = user_msg.lower()
            for k in keywords:
                if k in l:
                    title = k
                    break

        if not title:
            return {
                "final": "¿Qué recordatorio deseas quitar exactamente?",
                "action": None,
            }

        clean = title.strip()

        return {
            "final": f"De acuerdo, intento eliminar “{clean}”.",
            "action": {
                "type": "delete_reminder",
                "payload": {"title": clean},
            },
        }


    # ==============================================================
    # EDIT REMINDER — INTELIGENTE Y COMPLETO
    # ==============================================================
    def _handle_edit_reminder(self, user_msg: str, context: Dict[str, Any]):

        text = user_msg.lower()
        events = context.get("events", []) or []

        if not events:
            return {"final": "No tienes recordatorios para editar.", "action": None}

        # ===========================================================
        # 1) Encontrar cuál recordatorio quiere editar
        # ===========================================================
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

        # ===========================================================
        # 2) Extraer nueva info con EntityExtractor
        # ===========================================================
        now = datetime.utcnow()
        parsed = None
        try:
            parsed = self.extractor.extract_reminder(user_msg, now=now)
        except:
            parsed = None

        # Si extractor no devolvió nada útil → confirmar
        if not parsed:
            return {
                "final": (
                    f"¿Qué cambio deseas hacer en el recordatorio “{old_title}”? "
                    f"Puedes decir: “cámbialo para mañana a las 6” o “ponlo diario”."
                ),
                "action": None,
            }

        new_title = parsed.title or old_title
        new_dt = parsed.datetime
        new_repeats = parsed.repeats

        # ===========================================================
        # SIN FECHA → solo cambio de título
        # ===========================================================
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

        # ===========================================================
        # CON FECHA → edición completa
        # ===========================================================
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
                    "repeats": new_repeats,
                },
            ),
        }
