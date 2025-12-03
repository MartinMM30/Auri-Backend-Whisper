# auribrain/crisis_engine.py

from typing import Dict, Any

class CrisisEngine:
    """
    Detecta posibles crisis emocionales fuertes.
    NO reemplaza ayuda profesional. Solo contención + recomendación de buscar apoyo.
    """

    STRONG_PATTERNS = [
        "no quiero vivir",
        "no quiero seguir",
        "no aguanto más", "no aguanto mas",
        "ya no puedo más", "ya no puedo mas",
        "ya no quiero nada",
        "me quiero morir",
        "quisiera desaparecer",
        "no veo salida",
        "no tengo sentido",
    ]

    def detect(self, text: str, emotion_snapshot: Dict[str, Any]) -> bool:
        """
        Ahora recibe:
        - text
        - emotion_snapshot (energy, stress, overall)
        """

        t = (text or "").lower()

        # Crisis explícita detectada por texto
        if any(p in t for p in self.STRONG_PATTERNS):
            return True

        # Crisis emocional implícita
        emo = emotion_snapshot.get("overall", "neutral")
        energy = emotion_snapshot.get("energy", 0.5)
        stress = emotion_snapshot.get("stress", 0.3)

        # Muy triste + sin energía + mucho estrés = riesgo
        if emo in ["sad", "tired", "empathetic"] and energy < 0.25 and stress > 0.7:
            return True

        return False

    def respond(self, user_name: str | None = None) -> str:
        nombre = (user_name or "").strip()
        saludo = f"{nombre}, " if nombre else ""

        return (
            f"{saludo}siento muchísimo que estés pasando por algo tan pesado. 💔\n\n"
            "No tenés que cargar con esto solo. Estoy acá con vos.\n\n"
            "Lo que estás sintiendo es importante y válido. Hablarlo ya es un paso enorme.\n\n"
            "Si podés, buscá a alguien de confianza ahora mismo: familia, pareja, un amigo cercano.\n"
            "Si sentís que estás en peligro, por favor contactá a emergencias o una línea de ayuda inmediatamente.\n\n"
            "Mientras tanto, si querés… contame qué es lo que más te duele ahora mismo."
        )
