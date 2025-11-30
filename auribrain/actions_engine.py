# auribrain/actions_engine.py

from datetime import datetime
from typing import Any, Dict, Optional

from auribrain.entity_extractor import EntityExtractor, ExtractedReminder


class ActionsEngine:
  """
  Recibe:
    - intent (e.g. "reminder.create")
    - mensaje del usuario
    - contexto, memoria (opcional)
  Y devuelve:
    - final: texto final opcional para el usuario
    - action: diccionario con acción para Flutter (o None)
  """

  def __init__(self):
    self.extractor = EntityExtractor()

  # API principal usada por AuriMind
  def handle(
    self,
    intent: str,
    user_msg: str,
    context: Dict[str, Any],
    memory,
  ) -> Dict[str, Any]:
    if intent == "reminder.create":
      return self._handle_create_reminder(user_msg, context)

    if intent == "reminder.remove":
      return self._handle_delete_reminder(user_msg, context)

    # Otros intents futuros (pagos específicos, etc.)
    return {"final": None, "action": None}

  # ----------------------------------------------------------
  # CREATE REMINDER
  # ----------------------------------------------------------
  def _handle_create_reminder(self, user_msg: str, context: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(user_msg, now=now)

    if not parsed:
      # No pudo extraer nada fiable → sin acción, que responda normal
      return {
        "final": "Intenté entender el recordatorio, pero no me quedó claro. ¿Puedes repetirlo con fecha y hora?",
        "action": None,
      }

    if not parsed.datetime:
      # No hay fecha clara
      final = f"Entendí que quieres recordar: “{parsed.title}”. ¿Me dices para cuándo exactamente?"
      return {"final": final, "action": None}

    # Tenemos título y fecha/hora → generamos acción
    dt = parsed.datetime
    dt_iso = dt.isoformat()

    # Mensaje corto amigable
    fecha_legible = dt.strftime("%d/%m a las %H:%M")
    final = f"Listo, te recuerdo “{parsed.title}” el {fecha_legible}."

    action = {
      "type": "create_reminder",
      "payload": {
        "title": parsed.title,
        "datetime": dt_iso,
        "kind": parsed.kind,
        "repeats": parsed.repeats,
      },
    }

    return {"final": final, "action": action}

  # ----------------------------------------------------------
  # DELETE REMINDER
  # ----------------------------------------------------------
  def _handle_delete_reminder(self, user_msg: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Busca un título aproximado en el mensaje y pide borrar algo con ese título.
    Flutter se encarga de buscar el match real.
    """
    # Reutilizamos extractor para sacar un posible título
    parsed: Optional[ExtractedReminder] = self.extractor.extract_reminder(user_msg)

    title = None
    if parsed and parsed.title:
      title = parsed.title
    else:
      # fallback muy simple: después de "quita", "elimina", etc.
      lowered = user_msg.lower()
      for key in ["quita ", "elimina ", "borra ", "cancelar "]:
        if key in lowered:
          idx = lowered.index(key) + len(key)
          title = user_msg[idx:].strip()
          break

    if not title:
      return {
        "final": "¿Cuál recordatorio quieres que quite? Dímelo con el título aproximado.",
        "action": None,
      }

    final = f"Perfecto, intento quitar el recordatorio “{title}”."

    action = {
      "type": "delete_reminder",
      "payload": {
        "title": title,
      },
    }

    return {"final": final, "action": action}
