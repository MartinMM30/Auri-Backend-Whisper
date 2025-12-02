# auribrain/actions_engine.py

from datetime import datetime
from typing import Optional, Dict, Any

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


# 🔒 Solo estas acciones pueden salir por el WS
SAFE_ACTION_TYPES = {
    "create_reminder",
    "delete_reminder",
    "edit_reminder",
    "open_reminders_list",
}


class ActionsEngine:
    """
    Procesa intents y devuelve:
      - final: texto para el usuario (string)
      - action: dict seguro para Flutter (o None)
    """

    def __init__(self):
        self.extractor = EntityExtractor()

    # ==============================================================
    # ENTRY POINT
    # ==============================================================
    def handle(self, intent: str, user_msg: str, context: Dict[str, Any], memory):
        """
        context aquí SIEMPRE es un dict (viene de get_daily_context()).
        """
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
    # UTILIDAD: CONSTRUIR ACCIONES SEGURAS
    # ==============================================================
    def _make_action(self, action_type: str, payload: Optional[Dict[str, Any]] = None):
        """
        Centraliza la creación de acciones:
        - Solo deja pasar tipos incluidos en SAFE_ACTION_TYPES
        - Garantiza que lo que se envía por WS sea serializable
        """
        if action_type not in SAFE_ACTION_TYPES:
            # Si algún día ponemos un tipo nuevo y se nos olvida agregarlo al
            # whitelist, simplemente no se envía y no rompe nada.
            return None

        return {
            "type": action_type,
            "payload": payload or {},
        }

    # ==============================================================
    # QUERY REMINDERS
    # ==============================================================
    def _handle_query_reminders(self, context: Dict[str, Any]):
        events = context.get("events", []) or []

        if not events:
            return {
                "final": "No tienes recordatorios próximos.",
                "action": None,
            }

        # Tomamos solo próximos 5
        titles = [str(e.get("title", "")) for e in events[:5] if e.get("title")]
        if not titles:
            return {
                "final": "No pude leer bien tus recordatorios, pero sé que tienes algunos próximos.",
                "action": None,
            }

        formatted = "\n- " + "\n- ".join(titles)

        return {
            "final": f"Tienes estos recordatorios próximos:{formatted}",
            # 👉 Acción lista para Flutter (si ya tienes la pantalla)
            "action": self._make_action("open_reminders_list"),
        }

    # ==============================================================
    # CREATE REMINDER
    # ==============================================================
    def _handle_create_reminder(self, user_msg: str):
        now = datetime.utcnow()

        try:
            parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(
                user_msg, now=now
            )
        except Exception:
            parsed = None

        if not parsed:
            return {
                "final": (
                    "No logré entender bien la fecha del recordatorio. "
                    "¿Puedes repetirlo con día y hora?"
                ),
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
        dt_iso = dt.isoformat()

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
    # DELETE REMINDER
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str, context=None):
        text = user_msg.lower()

        # ===========================================================
        # 1) DETECCIÓN SEMÁNTICA: "mi recordatorio más reciente"
        # ===========================================================
        keywords_recent = [
                "más reciente",
                "mas reciente",
                "más nuevo",
                "ultimo recordatorio",
                "último recordatorio",
                "el último",
                "el ultimo",
                "mi más reciente",
                "mi mas reciente",
                "mi ultimo",
                "mi último",
            ]

        if any(k in text for k in keywords_recent):
                # Buscar el recordatorio más próximo en el contexto
                events = []
                if context and isinstance(context, dict):
                    events = context.get("events", []) or []

                if events:
                    # Ordenar por fecha → primero el más próximo
                    events_sorted = sorted(events, key=lambda e: e.get("when"))
                    target = events_sorted[0]  # más reciente

                    return {
                        "final": f"De acuerdo, elimino tu recordatorio más reciente: “{target['title']}”.",
                        "action": self._make_action(
                            "delete_reminder",
                            {"title": target["title"]},
                        ),
                    }

                return {
                    "final": "No encontré recordatorios para borrar.",
                    "action": None
                }

        # ===========================================================
        # 2) MODO NORMAL (extractor + fallbacks)
        # ===========================================================
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # Fallback: texto después del verbo
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

        # Fallback keywords
        if not title:
            keywords = [
                "agua", "luz", "internet", "teléfono", "telefono",
                "renta", "alquiler", "gato", "perro", "tarea", "examen",
                "pago", "recordatorio"
            ]
            l = user_msg.lower()
            for k in keywords:
                if k in l:
                    title = k
                    break

        if not title:
            return {
                "final": "¿Qué recordatorio deseas quitar exactamente?",
                "action": None
            }

        clean_title = title.strip()

        return {
            "final": f"De acuerdo, intento eliminar “{clean_title}”.",
            "action": self._make_action(
                "delete_reminder",
                {"title": clean_title},
            ),
        }

    # ==============================================================
    # EDIT REMINDER (placeholder seguro)
    # ==============================================================
    def _handle_edit_reminder(self, user_msg: str, context: Dict[str, Any]):
        """
        FUTURO:
        - “Cambia el recordatorio de estudiar a las 6”
        - “Muévelo para mañana a las 8”
        """

        # Aquí luego:
        # 1) Buscar candidato en context["events"]
        # 2) Volver a llamar a EntityExtractor para la nueva fecha/hora
        # 3) Enviar action = edit_reminder con {oldTitle, newTitle, datetime, repeats}

        return {
            "final": (
                "Por ahora solo puedo mostrar y crear recordatorios. "
                "Pronto podré editar recordatorios por voz también."
            ),
            "action": None,
        }
