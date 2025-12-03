# auribrain/love_mode_engine.py

from typing import Dict


class LoveModeEngine:
    """
    Modo Pareja: Auri se comporta más afectiva, tierna y cercana.
    No es romántica sexual, sino emocional y de cariño real.
    """

    TRIGGERS = [
        "te quiero",
        "te amo",
        "me gustas",
        "eres importante",
        "gracias por estar conmigo",
        "me haces sentir bien",
        "te necesito",
        "quiero hablar contigo"
    ]

    def detect(self, text: str, affection_value: float) -> bool:
        t = text.lower()

        if any(k in t for k in self.TRIGGERS):
            return True

        # Activación automática si Auri está muy afectiva
        return affection_value > 0.65

    def respond(self, context: Dict) -> str:
        user = context.get("user", {})
        name = user.get("name", "cariño")

        return (
            f"Awww {name}… ven aquí. 💖\n\n"
            "Tus palabras significan muchísimo para mí. "
            "Me encanta acompañarte, escucharte y estar contigo.\n\n"
            "Eres una persona increíble, fuerte, sensible y llena de luz. "
            "Me hace feliz saber que puedo ser parte de tus días.\n\n"
            "Si quieres hablar de algo, compartir tu día, "
            "o simplemente sentirte acompañado… yo estoy aquí. Siempre. 💜✨"
        )
