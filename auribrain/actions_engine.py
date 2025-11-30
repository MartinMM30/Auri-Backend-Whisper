# auribrain/actions_engine.py

from datetime import datetime
from typing import Dict, Any, Optional


class AuriActionsEngine:
    """
    Motor de acciones de Auri.
    Traduce intents en acciones reales.
    Todas las acciones retornan:
    - message: Para mostrar al usuario
    - action:  Evento opcional para el frontend
    """

    # ---------------------------------------------------------------
    # EJECUTOR PRINCIPAL
    # ---------------------------------------------------------------
    def execute(self, intent: str, entities: Dict[str, Any]) -> Optional[Dict]:
        print(f"[AuriActions] Intent: {intent}, Entities: {entities}")

        if intent == "weather.query":
            return self._weather_open()

        if intent == "outfit.suggest":
            return self._open_outfit()

        if intent == "reminder.create":
            return self._create_reminder(entities)

        if intent == "reminder.remove":
            return self._remove_reminder(entities)

        if intent == "emotion.support":
            return {"message": "Estoy aquí contigo 💜"}

        # No hay acción directa
        return None

    # ---------------------------------------------------------------
    # WEATHER — abre pantalla de clima
    # ---------------------------------------------------------------
    def _weather_open(self):
        return {
            "message": "Mostrando el clima 🌦️",
            "action": {"action": "open_weather"}
        }

    # ---------------------------------------------------------------
    # OUTFIT — sugiere ropa → abre pantalla
    # ---------------------------------------------------------------
    def _open_outfit(self):
        return {
            "message": "Veamos qué outfit te queda hoy ✨",
            "action": {"action": "open_outfit"}
        }

    # ---------------------------------------------------------------
    # RECORDATORIOS
    # ---------------------------------------------------------------

    def _create_reminder(self, entities: Dict[str, Any]):
        """
        Espera:
        {
            "title": "...",
            "datetime": "2025-02-15T09:00:00"
        }
        """

        title = entities.get("title")
        dt_iso = entities.get("datetime")

        if not title or not dt_iso:
            return {
                "message": "Creo que faltó la fecha u hora para ese recordatorio.",
            }

        try:
            dt = datetime.fromisoformat(dt_iso)
        except:
            return {"message": "No entendí bien la fecha, ¿puedes repetirla?"}

        # Aquí Auri debería guardar el recordatorio REAL en BD/Hive,
        # pero como este engine está en backend puro,
        # devolvemos un evento al frontend para que Flutter lo guarde.

        return {
            "message": f"Perfecto, te lo recuerdo el {dt.day}/{dt.month}.",
            "action": {
                "action": "create_reminder",
                "payload": {
                    "title": title,
                    "datetime": dt_iso
                }
            }
        }

    # ---------------------------------------------------------------

    def _remove_reminder(self, entities: Dict[str, Any]):
        """
        Espera:
        {
            "title": "...",
            "datetime": "...", (opcional)
        }
        """

        title = entities.get("title")

        if not title:
            return {"message": "¿Cuál recordatorio quieres eliminar exactamente?"}

        return {
            "message": f"Listo, quité el recordatorio de {title}.",
            "action": {
                "action": "delete_reminder",
                "payload": {"title": title}
            }
        }

