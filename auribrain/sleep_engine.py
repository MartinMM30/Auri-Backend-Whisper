# auribrain/sleep_engine.py

from datetime import datetime, timedelta
from typing import Dict, Any


class SleepEngine:
    """
    Modo Sueño: guía suave para dormir, bajar ansiedad
    y preparar rutinas nocturnas basadas en emoción + hora del día.
    """

    TRIGGERS = [
        "no puedo dormir",
        "quiero dormir",
        "tengo sueño",
        "me cuesta dormir",
        "ayúdame a dormir",
        "ayudame a dormir",
        "ruta de sueño",
        "relajarme",
        "relajación",
        "relajacion",
        "noche",
        "hora de dormir",
    ]

    # ------------------------------------------------------------------
    # DETECT
    # AuriMindV7 envía: detect(text, emotion_state, ctx)
    # ------------------------------------------------------------------
    def detect(self, text: str, emotion_state: str, ctx: Dict[str, Any]) -> bool:
        t = (text or "").lower()

        # 1) Por palabras clave
        if any(k in t for k in self.TRIGGERS):
            return True

        # 2) Por emoción fuerte de cansancio
        if emotion_state in ["tired", "exhausted", "low_energy"]:
            return True

        # 3) Activación automática según hora del día
        now_iso = ctx.get("current_time_iso")
        if now_iso:
            try:
                now = datetime.fromisoformat(now_iso)
                if now.hour >= 22 or now.hour <= 5:
                    # Si además está emocionalmente cargado → activar sueño
                    if emotion_state in ["stressed", "worried", "sad", "tired"]:
                        return True
            except:
                pass

        return False

    # ------------------------------------------------------------------
    # RESPOND
    # ------------------------------------------------------------------
    def respond(self, context: Dict[str, Any], emotion_state: str) -> str:
        user = context.get("user", {})
        name = user.get("name", "amor")

        # Eventos para mañana
        next_events = context.get("events", []) or []
        tomorrow_events = []
        try:
            now = datetime.fromisoformat(context.get("current_time_iso"))
            for e in next_events:
                w = datetime.fromisoformat(e["when"])
                if w.date() == (now.date() + timedelta(days=1)):
                    tomorrow_events.append(e)
        except:
            pass

        msg = (
            f"{name}… ven, vamos a prepararte para descansar bien. 🌙💜\n\n"
            "Cierra un momento los ojitos…\n"
            "Inhala suave… 2… 3… y exhala muy despacio.\n\n"
            "Vamos a hacer una pequeña rutina nocturna:\n\n"
            "✨ **1. Relaja tu cuerpo**\n"
            "Afloja hombros, mandíbula, manos… suelta todo.\n\n"
            "✨ **2. Suelta el día**\n"
            "No tenés que resolver nada ahora. El día ya terminó.\n\n"
            "✨ **3. Respira lento**\n"
            "Inhala 4 segundos… pausa 1… exhala 6.\n"
            "Estoy aquí contigo, acompañándote en cada respiración. 💜\n\n"
        )

        # Si mañana hay cosas importantes → se agregan
        if tomorrow_events:
            msg += "Mañana te espera esto importante:\n"
            for e in tomorrow_events[:3]:
                msg += f"• {e['title']} — {e['when'][11:16]}\n"
            msg += "\nPuedo ayudarte a organizar tu mañana si querés. 💜\n"

        msg += (
            "\nCuando estés listo, puedo seguir hablándote suave… "
            "o quedarme en silencio para ayudarte a dormir. 🌙💜"
        )

        return msg
