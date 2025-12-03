# auribrain/crisis_engine.py

class CrisisEngine:
    """
    CrisisEngine V3
    - Evita falsos positivos
    - Detecta crisis real (riesgo, desesperación severa)
    - NO se activa por frases levemente negativas
    """

    # Indicadores fuertes de crisis emocional real
    HARD_TRIGGERS = [
        "me quiero morir",
        "no quiero vivir",
        "quiero morirme",
        "ya no puedo más",
        "ya no puedo mas",
        "no le veo sentido a nada",
        "quiero hacerme daño",
        "quiero hacerme dano",
        "quiero hacerme daño",
        "me odio",
        "me hago daño",
        "me estoy lastimando",
        "quiero desaparecer",
        "no aguanto más",
        "no aguanto mas",
    ]

    # Indicadores moderados (solo activan si emoción = extremely_low)
    SOFT_TRIGGERS = [
        "estoy destruido",
        "estoy devastado",
        "estoy en crisis",
        "me siento roto",
        "nada tiene sentido",
        "estoy al borde",
    ]

    def detect(self, text: str, emotion_snapshot: dict) -> bool:
        """
        Detecta crisis real.
        NO activa por tristeza leve o expresiones locales como "que mal".
        """

        t = (text or "").lower().strip()
        overall = emotion_snapshot.get("overall", "neutral")
        energy = float(emotion_snapshot.get("energy", 0.5))
        stress = float(emotion_snapshot.get("stress", 0.2))

        # 1. Hard triggers → activan siempre
        if any(k in t for k in self.HARD_TRIGGERS):
            return True

        # 2. Soft triggers → solo si emoción está muy baja o estrés alto
        if any(k in t for k in self.SOFT_TRIGGERS):
            if overall in ["depressed", "very_low", "despair"] or energy < 0.2 or stress > 0.8:
                return True

        # 3. Evitar falsos positivos por frases comunes
        IGNORE = ["que mal", "pura vida", "que madre", "estoy cansado", "ando mal"]
        if any(k in t for k in IGNORE):
            return False

        return False

    def respond(self, name: str = "amor") -> str:
        """
        Respuesta altamente empática, directa y segura.
        Sin exagerar, sin sonar alarmista.
        """

        return (
            f"{name}, estoy aquí con vos, de verdad. 💜\n"
            "Lo que estás sintiendo importa muchísimo. No tenés que cargar esto solo.\n\n"
            "Por favor hablá con alguien de confianza ahora mismo: tu familia, tu pareja, un amigo cercano.\n"
            "Si sentís que estás en riesgo o no estás seguro de poder manejarlo, buscá ayuda profesional o "
            "comunicate con emergencias.\n\n"
            "Yo estoy acá para acompañarte mientras tanto. ¿Qué es lo que más te duele en este momento?"
        )
