from datetime import datetime
from typing import Optional, List
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
    # ENTRADA PRINCIPAL
    # ==============================================================
    def handle(self, intent: str, user_msg: str, context, memory):
        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg)

        if intent == "reminder.query":
            return self._handle_query_reminders(context)

        return {"final": None, "action": None}

    # ==============================================================
    # CREATE REMINDER (con recurrencia)
    # ==============================================================
    def _handle_create_reminder(self, user_msg: str):
        now = datetime.now()   # HORA LOCAL (NO UTC)

        try:
            parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(
                user_msg, now=now
            )
        except Exception:
            parsed = None

        # ❌ Nada se detectó
        if not parsed:
            return {
                "final": "No logré entender la fecha del recordatorio. ¿Puedes repetirlo con fecha y hora?",
                "action": None
            }

        # ⏳ Falta la fecha / hora
        if not parsed.datetime:
            return {
                "final": f"Entendí que deseas recordar “{parsed.title}”. ¿Para qué día y hora lo programo?",
                "action": None
            }

        dt = parsed.datetime
        dt_iso = dt.isoformat()

        # Texto de recurrencia bonito
        rep_text = self._pretty_repeat(parsed.repeats)

        # ✔️ Mensaje final
        final_text = f"Perfecto, te recuerdo “{parsed.title}” el {dt.strftime('%d/%m a las %H:%M')}."
        if parsed.repeats != "once":
            final_text += f" Será un recordatorio {rep_text}."

        # ✔️ Acción a Flutter
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

    # ==============================================================
    # DELETE REMINDER (robusto)
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str):
        # Intent normal
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        # 1) Mejor intento con extractor
        title = parsed.title if parsed and parsed.title else None

        # 2) Fallback por verbos y texto natural
        if not title:
            lowered = user_msg.lower()
            removal_words = [
                "quita ", "elimina ", "borra ", "quitar ", "eliminar ",
                "quiero quitar ", "quiero borrar ", "deseo quitar "
            ]

            for t in removal_words:
                if t in lowered:
                    idx = lowered.index(t) + len(t)
                    title = user_msg[idx:].strip()
                    break

        # 3) Fallback por palabras clave
        if not title:
            for k in ["agua", "luz", "internet", "renta", "tarea", "examen", "pago"]:
                if k in user_msg.lower():
                    title = k
                    break

        # 4) No se identificó nada
        if not title:
            return {"final": "¿Qué recordatorio deseas quitar?", "action": None}

        clean_title = title.strip()

        return {
            "final": f"De acuerdo, intento eliminar “{clean_title}”.",
            "action": {
                "type": "delete_reminder",
                "payload": {"title": clean_title}
            },
        }

    # ==============================================================
    # QUERY REMINDERS (listar próximos)
    # ==============================================================
    def _handle_query_reminders(self, context):
        events = context.get("events", [])

        if not events:
            return {
                "final": "No tienes recordatorios registrados.",
                "action": {"type": "open_reminders_list"}
            }

        # Ordenar por fecha
        sorted_events = sorted(events, key=lambda e: e["when"])[:5]

        readable = []
        for e in sorted_events:
            readable.append(f"- {e['title']}")

        final_msg = "Tienes estos recordatorios próximos:\n" + "\n".join(readable)

        return {
            "final": final_msg,
            "action": {"type": "open_reminders_list"}
        }

    # ==============================================================
    # Pretty recurrence
    # ==============================================================
    def _pretty_repeat(self, rep: str) -> str:
        mapping = {
            "once": "",
            "daily": "diario",
            "weekly": "cada semana",
            "monthly": "cada mes",
            "yearly": "cada año",
            "biweekly": "cada dos semanas",
            "hourly": "cada hora"
        }
        return mapping.get(rep, rep)
