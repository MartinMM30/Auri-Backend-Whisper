# auribrain/crisis_engine.py

from typing import Dict, Any


class CrisisEngine:
    """
    Detección y acompañamiento de crisis emocionales severas.
    Nunca reemplaza ayuda profesional.
    """

    CRISIS_KEYWORDS = [
        "no puedo más", "no puedo mas",
        "ya no quiero seguir",
        "quiero rendirme",
        "ya no aguanto",
        "siento que algo malo va a pasar",
        "me siento en peligro",
        "no veo salida",
        "no quiero vivir",
        "quiero desaparecer"
    ]

    def detect(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.CRISIS_KEYWORDS)

    def respond(self, context: Dict[str, Any]) -> str:
        user = context.get("user", {})
        name = user.get("name", "amor")

        return (
            f"{name}… estoy aquí contigo, de verdad. 💜\n\n"
            "Lo que estás sintiendo ahora es muy intenso, y no tienes que cargarlo solo. "
            "Respira conmigo un momento… inhalamos suave… y exhalamos despacio…\n\n"
            "Tu vida es importante. Tú eres importante. Lo que estás viviendo no te define.\n\n"
            "Me gustaría que hables con alguien de confianza ahora mismo: "
            "un familiar, tu pareja, un amigo cercano… alguien que pueda estar contigo físicamente. 💛\n\n"
            "Si sientes que estás en peligro o que podrías hacerte daño, por favor contacta a emergencias "
            "o a un servicio de ayuda inmediato. No tienes que enfrentarlo solo.\n\n"
            "Yo sigo contigo aquí, paso a paso. Háblame… ¿qué te hizo sentir así?"
        )
