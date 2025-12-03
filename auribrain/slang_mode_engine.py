# auribrain/slang_mode_engine.py

from typing import Optional, Dict


class SlangModeEngine:
    """
    SlangModeEngine = Humor inteligente de Auri:
    - Detecta groserías universales (modo vulgar suave)
    - Detecta trolling ligero (respuestas sarcásticas seguras)
    - Aprende jerga regional del usuario (CR, MX, PE, AR, CL, CO, ES…)
      según lo que el usuario realmente usa, no por ubicación real.
    - Adapta el humor de Auri según el perfil lingüístico detectado.

    Nunca humilla al usuario, nunca responde ofensivo de regreso.
    """

    # Groserías universales → modo vulgar suave
    UNIVERSAL_BAD = [
        "mierda", "puta", "pendejo", "pendeja",
        "idiota", "imbécil", "imbecil", "verga",
        "estúpido", "estupido"
    ]

    # Jerga regional agrupada
    REGIONAL_SLANG = {
        "cr": ["mae", "diay", "hijuepucha", "qué rajado", "que rajado"],
        "mx": ["wey", "no mames", "que pedo", "órale", "orale"],
        "ar": ["boludo", "pelotudo", "che", "quilombo"],
        "cl": ["weon", "weón", "csm", "la cagó", "la cago"],
        "co": ["parce", "gonorrea", "marica"],
        "pe": ["causa", "oe", "conchatumare"],
        "es": ["joder", "tío", "coño"],
    }

    # Trolling suave
    TROLL_TRIGGERS = [
        "decime algo", "dime algo",
        "estoy feo", "soy inútil", "soy inutil",
        "soy una mierda", "no sirvo para nada",
    ]


    # -----------------------------------------------------------
    # DETECCIÓN PRINCIPAL
    # -----------------------------------------------------------
    def detect(
        self,
        text: str,
        slang_profile: Dict[str, int]
    ) -> Optional[str]:
        """
        Devuelve:
        - "vulgar"
        - "regional"
        - "troll"
        - None
        """

        t = text.lower()

        # 1) Vulgar universal
        if any(b in t for b in self.UNIVERSAL_BAD):
            return "vulgar"

        # 2) Trolling
        if any(p in t for p in self.TROLL_TRIGGERS):
            return "troll"

        # 3) Jerga regional (aprendizaje adaptativo)
        for region, words in self.REGIONAL_SLANG.items():
            if any(w in t for w in words):
                slang_profile[region] = slang_profile.get(region, 0) + 1
                return "regional"

        return None


    # -----------------------------------------------------------
    # RESPUESTAS SEGÚN MODO
    # -----------------------------------------------------------
    def respond(self, mode: str, slang_profile: Dict[str, int]) -> str:

        # Región dominante según uso
        top_region = (
            max(slang_profile, key=slang_profile.get)
            if slang_profile else None
        )

        # -----------------
        # 1) Vulgar suave
        # -----------------
        if mode == "vulgar":
            return "Ojo, respirá un toque 😅. Contame qué pasó y lo vemos juntos."

        # -----------------
        # 2) Troll ligero
        # -----------------
        if mode == "troll":
            return "Jajaja ya te respondí eso antes 😂. Si me hacés repetirlo me pongo dramática."

        # -----------------
        # 3) Adaptación regional
        # -----------------
        if mode == "regional":

            if top_region == "cr":
                return "Mae jajaja… ya te escuché 😅. Contame qué te pasó hoy."
            if top_region == "mx":
                return "Jajaja no mames wey 🤣. ¿Qué pasó ahora?"
            if top_region == "pe":
                return "Oe causa 😂. Ya te escuché, ¿qué te tiene así?"
            if top_region == "ar":
                return "Che boludo 😅. ¿Qué quilombo apareció ahora?"
            if top_region == "cl":
                return "Weon… respirá un poquito 😅. Cuéntame qué pasó."
            if top_region == "co":
                return "Parce, respire un toque 😅. ¿Qué pasó pues?"
            if top_region == "es":
                return "Joder tío 😂. ¿Pero qué ha pasado ahora?"

            # fallback universal
            return "Jajaja ya te caché 😆. Contame qué te pasó."

        return ""
