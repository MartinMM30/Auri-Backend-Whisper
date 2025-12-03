# auribrain/mental_health_engine.py

class MentalHealthEngine:
    """Modo Salud Mental (leve, preventivo)."""

    KEYWORDS = [
        "ansioso", "ansiosa", "ansiedad",
        "estresado", "estresada", "estres",
        "no puedo más", "no puedo mas",
        "agotado", "agotada",
        "abrumado", "abrumada",
        "me siento mal conmigo",
    ]

    def detect(self, text: str, stress_level: float) -> bool:
        t = (text or "").lower()

        if any(k in t for k in self.KEYWORDS):
            return True

        return stress_level > 0.6

    def respond(self) -> str:
        return (
            "Entiendo que te sientas así… de verdad. No es poca cosa cargar con todo eso. 💜\n\n"
            "Probemos algo sencillo: inhalá profundo por 4 segundos, sostené 4, exhalá en 6…\n"
            "Si querés, puedo ayudarte a ordenar tu día para que no se sienta tan pesado."
        )
