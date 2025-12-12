# auribrain/crisis_engine.py

class CrisisEngine:
    """
    CrisisEngine V3.5 — cero falsos positivos
    - Ignora gustos, preferencias y frases neutrales
    - Soft triggers SOLO si emoción = crítico + texto muy claro
    """

    HARD_TRIGGERS = [
        "me quiero morir",
        "no quiero vivir",
        "quiero morirme",
        "ya no puedo más",
        "ya no puedo mas",
        "no le veo sentido a nada",
        "quiero hacerme daño",
        "quiero hacerme dano",
        "me hago daño",
        "me estoy lastimando",
        "quiero desaparecer",
        "no aguanto más",
        "no aguanto mas",
    ]

    # Soft triggers más estrictos
    SOFT_TRIGGERS = [
        "estoy destruido",
        "estoy devastado",
        "estoy en crisis",
        "me siento roto",
        "nada tiene sentido",
        "estoy al borde",
    ]

    # Frases que JAMÁS deben activar crisis
    SAFE_CONTEXT = [
        "mi color favorito",
        "me encanta",
        "odio levantarme temprano",
        "amo",
        "me gusta",
        "estoy estudiando",
        "mi comida favorita",
        "mi perro",
        "mi mamá",
        "mi papá",
        "mi hermano",
        "mi tía",
        "anime",
        "juegos",
        "películas",
        "gustaría",
        "quiero aprender",
        "estoy cansado",
        "ando mal",
        "estoy triste",
        "estoy bajoneado",
    ]

    def detect(self, text: str, emotion_snapshot: dict) -> bool:
        t = (text or "").lower().strip()

        # 🔹 Si el texto pertenece a un contexto seguro, NO hay crisis.
        if any(s in t for s in self.SAFE_CONTEXT):
            return False

        overall = emotion_snapshot.get("overall", "neutral")
        energy = float(emotion_snapshot.get("energy", 0.5))
        stress = float(emotion_snapshot.get("stress", 0.2))

        # 1) Triggers duros
        if any(k in t for k in self.HARD_TRIGGERS):
            return True

        # 2) Soft triggers pero SOLO si emoción muy baja
        if any(k in t for k in self.SOFT_TRIGGERS):
            if overall in ["depressed", "very_low", "despair"] and (energy < 0.25 or stress > 0.75):
                return True

        return False
