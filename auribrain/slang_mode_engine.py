# auribrain/slang_mode_engine.py

class SlangModeEngine:
    """
    Modo vocabulario soez / humor negro suave.
    No es ofensiva, pero sí más directa, sarcástica y "realista".
    """

    BAD_WORDS = [
        "puta", "mierda", "verga", "hijueputa", "hijo de puta",
        "idiota", "imbécil", "imbecil", "estúpido", "estupido",
        "guevón", "guevon", "pendejo", "pendeja",
    ]

    TROLL_PATTERNS = [
        "decime algo", "dime algo",
        "estoy feo", "soy inútil", "soy inutil",
        "soy una mierda", "no sirvo para nada",
    ]

    def detect(self, text: str, stress_level: float) -> str | None:
        t = (text or "").lower()

        if any(b in t for b in self.BAD_WORDS):
            return "slang"

        if any(p in t for p in self.TROLL_PATTERNS):
            return "troll"

        # si el usuario está muy cargado, Auri se vuelve un poquito más directa
        if stress_level > 0.75:
            return "direct"

        return None

    def respond(self, mode: str) -> str:
        if mode == "slang":
            return (
                "Mae, respirá un toque 😅. Entiendo que estés molesto, pero contame bien qué pasó "
                "y vemos cómo te puedo ayudar en serio."
            )

        if mode == "troll":
            return (
                "Jajaja, ya te respondí eso antes, ¿ves? 😂 "
                "Si me hacés repetirlo mucho voy a empezar a cobrar en café."
            )

        if mode == "direct":
            return (
                "Ok, te siento MUY cargado. No voy a regañarte, pero sí te digo algo directo: "
                "tu bienestar importa más que todo este enredo. Contame qué pasa."
            )

        return ""
