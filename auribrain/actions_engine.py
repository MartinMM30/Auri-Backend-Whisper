# auribrain/actions_engine.py

from datetime import datetime
from typing import Optional, Dict, Any

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


# 🔒 Tipos de acción permitidos hacia Flutter
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
    """
    Procesa intents y devuelve:
      - final: texto para el usuario (string)
      - action: dict seguro para Flutter (o None)
    """

    def __init__(self):
        self.extractor = EntityExtractor()
        # Recordatorio pendiente de confirmación (para reminder.confirm)
        self.pending_reminder: Optional[Dict[str, Any]] = None

    # ==============================================================
    # UTIL: obtener "ahora" real del usuario según el contexto
    # ==============================================================
    def _get_now(self, context: Dict[str, Any]) -> datetime:
        iso = context.get("current_time_iso")
        if iso:
            try:
                return datetime.fromisoformat(iso)
            except Exception:
                pass
        # fallback
        return datetime.now()

    # ==============================================================
    # UTIL: construir acción segura
    # ==============================================================
    def _make_action(
        self, action_type: str, payload: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if action_type not in SAFE_ACTION_TYPES:
            return None
        return {
            "type": action_type,
            "payload": payload or {},
        }

    # ==============================================================
    # ENTRY POINT
    # ==============================================================
    def handle(
        self,
        intent: str,
        user_msg: str,
        context: Dict[str, Any],
        memory,
    ):
        # context aquí SIEMPRE es un dict (viene de get_daily_context()).

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

        # Otros intents los maneja el modelo de conversación normal
        return {"final": None, "action": None}

    # ==============================================================
    # QUERY REMINDERS
    # ==============================================================
    def _handle_query_reminders(self, context: Dict[str, Any]):
        events = context.get("events", []) or []

        if not events:
            return {"final": "No tienes recordatorios próximos.", "action": None}

        titles = [str(e.get("title", "")).strip() for e in events[:5] if e.get("title")]
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
    # CREATE REMINDER (con pending_reminder)
    # ==============================================================
    def _handle_create_reminder(self, user_msg: str, context: Dict[str, Any]):
        now = self._get_now(context)

        try:
            parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(
                user_msg, now=now
            )
        except Exception:
            parsed = None

        if not parsed:
            # Nada entendible → pedir que repita con fecha/hora
            self.pending_reminder = None
            return {
                "final": (
                    "No logré entender bien la fecha del recordatorio. "
                    "¿Puedes repetirlo con día y hora?"
                ),
                "action": None,
            }

        # Si NO hay datetime → guardamos pending_reminder y pedimos confirmación
        if not parsed.datetime:
            self.pending_reminder = {
                "title": parsed.title,
                "kind": parsed.kind,
                "repeats": parsed.repeats,
            }
            return {
                "final": (
                    f"Entendí que deseas recordar “{parsed.title}”. "
                    "¿Para qué día y hora lo programo?"
                ),
                "action": None,
            }

        # Si sí hay datetime → creamos directo y limpiamos pending
        dt = parsed.datetime
        dt_iso = dt.isoformat()
        self.pending_reminder = None

        return {
            "final": (
                f"Perfecto, te recuerdo “{parsed.title}” "
                f"el {dt.strftime('%d/%m a las %H:%M')}."
            ),
            "action": self._make_action(
                "create_reminder",
                {
                    "title": parsed.title,
                    "datetime": dt_iso,
                    "kind": parsed.kind,
                    "repeats": parsed.repeats,
                },
            ),
        }

    # ==============================================================
    # CONFIRM REMINDER (usa pending_reminder)
    # ==============================================================
    def _handle_confirm_reminder(self, user_msg: str, context: Dict[str, Any]):
        if not self.pending_reminder:
            return {
                "final": (
                    "No tengo ningún recordatorio pendiente por confirmar. "
                    "Si quieres, dime de nuevo qué quieres recordar."
                ),
                "action": None,
            }

        base = self.pending_reminder
        title = base["title"]
        kind = base["kind"]
        repeats = base["repeats"]

        now = self._get_now(context)

        # Intentamos extraer SOLO fecha/hora nueva desde la respuesta
        parsed = None
        try:
            parsed = self.extractor.extract_reminder(user_msg, now=now)
        except Exception:
            parsed = None

        # Si el usuario solo dijo “sí”, “ok”, etc → parsed será None o sin datetime
        if not parsed or not parsed.datetime:
            return {
                "final": (
                    f"Necesito al menos un día y una hora para “{title}”. "
                    "Por ejemplo: “mañana a las 8 de la noche”."
                ),
                "action": None,
            }

        dt = parsed.datetime
        dt_iso = dt.isoformat()

        # Si el modelo detectó un repeats mejor, lo usamos
        if parsed.repeats:
            repeats = parsed.repeats

        self.pending_reminder = None

        return {
            "final": (
                f"Listo, te recuerdo “{title}” "
                f"el {dt.strftime('%d/%m a las %H:%M')}."
            ),
            "action": self._make_action(
                "create_reminder",
                {
                    "title": title,
                    "datetime": dt_iso,
                    "kind": kind,
                    "repeats": repeats,
                },
            ),
        }

    # ==============================================================
    # DELETE REMINDER — con filtros extendidos
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str, context: Dict[str, Any] = None):
        text = user_msg.lower()
        events = []
        if context and isinstance(context, dict):
            events = context.get("events", []) or []

        # -------------------------
        def sort_events(ev_list):
            try:
                return sorted(ev_list, key=lambda e: e.get("when", ""))
            except Exception:
                return ev_list

        # 1) BORRAR TODOS
        if any(k in text for k in ["borra todos", "elimina todos", "quitar todos"]):
            return {
                "final": "Elimino todos tus recordatorios.",
                "action": self._make_action(
                    "delete_all_reminders",
                    {"confirmed": True},   # ← FIX DEFINITIVO
                ),
            }


        # 2) BORRAR POR CATEGORÍA
        if "pago" in text or "pagos" in text:
            return {
                "final": "De acuerdo, elimino tus recordatorios de pagos.",
                "action": self._make_action(
                    "delete_category",
                    {"category": "payment"},
                ),
            }

        if "cumple" in text or "cumpleaños" in text:
            return {
                "final": "Elimino tus recordatorios de cumpleaños.",
                "action": self._make_action(
                    "delete_category",
                    {"category": "birthday"},
                ),
            }

        # 3) BORRAR HOY / MAÑANA
        if "de hoy" in text or "hoy" in text:
            return {
                "final": "Elimino tus recordatorios de hoy.",
                "action": self._make_action(
                    "delete_by_date",
                    {"when": "today"},
                ),
            }

        if "de mañana" in text or "mañana" in text:
            return {
                "final": "Elimino tus recordatorios de mañana.",
                "action": self._make_action(
                    "delete_by_date",
                    {"when": "tomorrow"},
                ),
            }

        # 4) BORRAR MÁS PRÓXIMO
        keywords_next = [
            "próximo",
            "proximo",
            "el que sigue",
            "el que viene",
            "siguiente",
        ]
        if any(k in text for k in keywords_next):
            if events:
                sorted_events = sort_events(events)
                target = sorted_events[0]
                return {
                    "final": f"Elimino tu próximo recordatorio: “{target['title']}”.",
                    "action": self._make_action(
                        "delete_reminder",
                        {"title": target["title"]},
                    ),
                }
            return {
                "final": "No encontré recordatorios próximos para borrar.",
                "action": None,
            }

        # 5) BORRAR MÁS RECIENTE (equivalente semántico)
        keywords_recent = [
            "más reciente",
            "mas reciente",
            "más nuevo",
            "mas nuevo",
            "ultimo",
            "último",
            "el más reciente",
            "el mas reciente",
        ]
        if any(k in text for k in keywords_recent):
            if events:
                sorted_events = sort_events(events)
                target = sorted_events[0]
                return {
                    "final": (
                        f"Elimino tu recordatorio más reciente: “{target['title']}”."
                    ),
                    "action": self._make_action(
                        "delete_reminder",
                        {"title": target["title"]},
                    ),
                }
            return {
                "final": "No encontré recordatorios recientes para borrar.",
                "action": None,
            }

        # 6) BORRAR POR TÍTULO — extractor + fallbacks
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # Fallback texto después del verbo
        if not title:
            lowered = user_msg.lower()
            triggers = [
                "quita ",
                "borra ",
                "elimina ",
                "quiero quitar ",
                "quiero borrar ",
                "quiero eliminar ",
                "quita el ",
                "quita la ",
                "elimina el ",
                "elimina la ",
            ]
            for t in triggers:
                if t in lowered:
                    idx = lowered.index(t) + len(t)
                    title = user_msg[idx:].strip()
                    break

        # Fallback palabras clave
        if not title:
            keywords = [
                "agua",
                "luz",
                "internet",
                "teléfono",
                "telefono",
                "renta",
                "alquiler",
                "gato",
                "perro",
                "tarea",
                "examen",
                "pago",
                "recordatorio",
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
            "action": self._make_action(
                "delete_reminder",
                {"title": clean},
            ),
        }

    # ==============================================================
    # EDIT REMINDER — edición inteligente básica
    # ==============================================================
    def _handle_edit_reminder(self, user_msg: str, context: Dict[str, Any]):
        """
        Ejemplos:
        - “Cambia el recordatorio de estudiar a las 6”
        - “Muévelo para mañana a las 8”
        - “Haz que sea diario”
        """

        text = user_msg.lower()
        events = context.get("events", []) or []

        if not events:
            return {
                "final": "No tienes recordatorios para editar.",
                "action": None,
            }

        # 1) Intentar encontrar cuál recordatorio menciona el usuario
        target_event = None
        for ev in events:
            title = (ev.get("title") or "").lower()
            if title and title in text:
                target_event = ev
                break

        # Si no se detecta por título literal, cogemos el más próximo
        if not target_event:
            return {
                "final": (
                    "¿Cuál recordatorio deseas cambiar exactamente? "
                    "Puedes decir, por ejemplo: “cambia el de luz para mañana a las 6”."
                ),
                "action": None,
            }

        old_title = target_event.get("title", "")
        old_when = target_event.get("when", "")
        old_repeats = target_event.get("repeats", "once")

        now = self._get_now(context)

        # 2) Extraer nueva info con EntityExtractor
        parsed = None
        try:
            parsed = self.extractor.extract_reminder(user_msg, now=now)
        except Exception:
            parsed = None

        # Si el extractor no entiende nada → pedimos aclaración
        if not parsed:
            return {
                "final": (
                    f"¿Qué cambio deseas hacer en el recordatorio “{old_title}”? "
                    "Puedes decir: “cámbialo para mañana a las 6” o “hazlo diario”."
                ),
                "action": None,
            }

        new_title = parsed.title or old_title
        new_dt = parsed.datetime
        new_repeats = parsed.repeats or old_repeats

        # Caso A: solo cambia el nombre (sin nueva fecha)
        if not new_dt and new_title != old_title:
            return {
                "final": f"Perfecto, actualizo el nombre a “{new_title}”.",
                "action": self._make_action(
                    "edit_reminder",
                    {
                        "oldTitle": old_title,
                        "newTitle": new_title,
                        "datetime": old_when,
                        "repeats": old_repeats,
                    },
                ),
            }

        # Caso B: solo cambia repetición (“hazlo diario”, “cada semana”)
        if new_dt is None and new_repeats != old_repeats:
            return {
                "final": (
                    f"Listo, hago “{old_title}” un recordatorio "
                    f"{'diario' if new_repeats=='daily' else 'recurrente'}."
                ),
                "action": self._make_action(
                    "edit_reminder",
                    {
                        "oldTitle": old_title,
                        "newTitle": new_title,
                        "datetime": old_when,
                        "repeats": new_repeats,
                    },
                ),
            }

        # Caso C: cambio completo (fecha/hora, nombre, repetición…)
        if new_dt:
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

        # Fallback: nada claro que editar
        return {
            "final": (
                f"No estoy segura de qué cambiar en “{old_title}”. "
                "¿Quieres modificar la fecha, la hora, el nombre o que sea repetitivo?"
            ),
            "action": None,
        }
