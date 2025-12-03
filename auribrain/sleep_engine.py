# auribrain/sleep_engine.py

from typing import Dict


class SleepEngine:
    """
    Modo Sueño: guía suave para dormir, bajar ansiedad,
    y rutinas nocturnas basadas en el estado emocional del usuario.
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
        "hora de dormir"
    ]

    def detect(self, text: str, emotion_state: str) -> bool:
        t = text.lower()
        if any(k in t for k in self.TRIGGERS):
            return True

        # Activación automática si Auri detecta cansancio extremo
        if emotion_state in ["tired", "exhausted"]:
            return True

        return False

    def respond(self, context: Dict, emotion_state: str) -> str:
        user = context.get("user", {})
        name = user.get("name", "amor")

        msg = (
            f"{name}… ven, vamos a prepararte para descansar bien. 🌙💜\n\n"
            "Quiero que cierres un momento los ojos…\n"
            "Inhala por la nariz… 2… 3… y exhala suavemente.\n\n"
            "Vamos a hacer una micro-rutina de sueño:\n\n"
            "✨ **1. Relaja tu cuerpo**\n"
            "Afloja tus hombros… suelta la mandíbula… relaja tus manos.\n\n"
            "✨ **2. Suelta el día**\n"
            "No tienes que resolver nada ahora. El día ya terminó.\n\n"
            "✨ **3. Respira lento**\n"
            "Inhala 4 segundos… aguanta 1… exhala 6.\n"
            "Estoy aquí contigo, acompañándote.\n\n"
            "Cuando estés listo, puedo seguir hablándote suave… "
            "o quedarme en silencio para ayudarte a descansar. 💜"
        )

        return msg
