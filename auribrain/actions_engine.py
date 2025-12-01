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
    # PUNTO PRINCIPAL
    # ==============================================================
    def handle(self, intent: str, user_msg: str, context, memory):
        if intent == "reminder.create":
            return self._handle_create_reminder(user_msg)

        if intent == "reminder.remove":
            return self._handle_delete_reminder(user_msg)

        return {"final": None, "action": None}

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
    # DELETE REMINDER (MEGA FIX)
    # ==============================================================
       # ==============================================================
    # DELETE REMINDER (FIX)
    # ==============================================================
    def _handle_delete_reminder(self, user_msg: str):
        """
        FIX:
        - Si EntityExtractor falla → fallback automático
        - Limpia frases como:
            "el recordatorio de", "el recordatorio del",
            "recordatorio de", "recordatorio del"
        - No necesita fecha para borrar: sólo el título aproximado
        """

        # 1) Intentar extracción normal
        try:
            parsed = self.extractor.extract_reminder(user_msg)
        except Exception:
            parsed = None

        title = parsed.title if parsed and parsed.title else None

        # 2) Fallback: texto después de verbos típicos
        if not title:
            lowered = user_msg.lower()

            triggers = [
                "quita ", "elimina ", "borra ",
                "quiero quitar ", "quiero eliminar ", "quiero borrar ",
                "deseo quitar ", "deseo eliminar ", "deseo borrar ",
                "quiero borrar ", "deseo borrar ",
                "quita el ", "quita la ", "elimina el ", "elimina la ",
            ]

            for t in triggers:
                if t in lowered:
                    idx = lowered.index(t) + len(t)
                    title = user_msg[idx:].strip()
                    break

        # 3) Limpieza extra de "recordatorio de..."
        if title:
            raw = title.strip().lower()

            prefixes = [
                "el recordatorio de ",
                "el recordatorio del ",
                "el recordatorio ",
                "recordatorio de ",
                "recordatorio del ",
                "recordatorio ",
            ]
            for p in prefixes:
                if raw.startswith(p):
                    raw = raw[len(p):].strip()
                    break

            # Quitar "de " sobrante al inicio (ej: "de pagar la renta")
            if raw.startswith("de "):
                raw = raw[3:]

            # Quitar punto final
            if raw.endswith("."):
                raw = raw[:-1].strip()

            title = raw

        # 4) Fallback ultra simple: palabras clave
        if not title:
            lowered = user_msg.lower()
            for k in ["agua", "luz", "internet", "teléfono", "telefono", "renta", "gato"]:
                if k in lowered:
                    title = k
                    break

        # 5) Si AÚN no hay título
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
