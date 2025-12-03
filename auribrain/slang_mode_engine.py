# auribrain/slang_mode_engine.py

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re
import time


class SlangModeEngine:
    """
    SlangModeEngine V4 — Jerga Adaptativa Global

    Objetivos:
    - Aprender automáticamente la jerga del usuario.
    - Soportar tico, mexicano, peruano, colombiano, chileno, argentino, español, venezolano, dominicano, etc.
    - Usar jerga SOLO hacia el usuario si él también la usa.
    - No insultar nunca.
    - No activar humor cuando el usuario está enojado o frustrado (via flags).
    - Distinguir entre:
        - broma (friendly_slang)
        - frustración general (frustrated)
        - molestia hacia Auri (angry_at_auri)
        - expresión cultural fuerte (cultural_strong)

    API pública:
    - detect(text: str, slang_profile: dict) -> Optional[str]
      Devuelve uno de:
        "friendly_slang"
        "frustrated"
        "angry_at_auri"
        "cultural_strong"
        None (si no detecta nada relevante)

    - respond(mode: Optional[str], slang_profile: dict) -> str
      Devuelve una respuesta corta adaptada al modo y al perfil.
    """

    # -----------------------------
    # Diccionarios de jerga
    # -----------------------------

    # Groserías universales (sirven como señal de frustración / intensidad)
    UNIVERSAL_BAD = [
        "mierda", "puta", "pendejo", "pendeja",
        "idiota", "imbécil", "imbecil", "verga",
        "estúpido", "estupido", "cagada", "coñazo",
    ]

    # Jerga regional agrupada
    COUNTRY_SLANG = {
        "tico": [
            "mae", "tuanis", "pura vida", "playo", "diay", "que rajado", "qué rajado", "chiva",
        ],
        "mex": [
            "wey", "güey", "no mames", "órale", "orale", "chido", "chingón", "chingon", "carnal",
        ],
        "arg": [
            "boludo", "boluda", "che", "re loco", "quilombo", "posta", "bancá", "banca",
        ],
        "per": [
            "causa", "mano", "alucina", "chévere", "chevere", "pata", "oe", "habla causa",
        ],
        "col": [
            "parce", "gonorrea", "guevón", "guevon", "re duro", "que chimba", "melo",
        ],
        "chi": [
            "weon", "weón", "culiao", "la raja", "bacán", "bacan", "cachai",
        ],
        "ven": [
            "chamo", "pana", "verga", "arrecho", "burda", "echarle bolas",
        ],
        "dom": [
            "manín", "manin", "vaina", "durísimo", "durisimo", "pila", "jevi", "tíguere", "tiguere",
        ],
        "es-es": [
            "tío", "tio", "colega", "tronco de", "guay", "mola", "qué pasada", "que pasada", "joder", "coño",
        ],
    }

    # Trolling / autodesprecio suave (se puede tratar como broma + contención)
    TROLL_TRIGGERS = [
        "decime algo", "dime algo",
        "estoy feo", "soy feo", "soy fea",
        "soy inútil", "soy inutil",
        "soy una mierda", "no sirvo para nada",
    ]

    # Expresiones de buena onda / risa
    FRIENDLY_MARKERS = [
        "jaja", "jajaja", "xd", "xddd", "jsjs", "jeje", "😂", "🤣", "😅", "😆", "😜",
    ]

    # Frustración general
    FRUSTRATION_MARKERS = [
        "qué mierda", "que mierda", "que porquería", "que porqueria",
        "estoy harto", "estoy harta", "me frustra", "me estresa",
        "no sirve", "no sirve para nada", "esto no funciona",
    ]

    # Molestia directa hacia Auri (regaño)
    ANGRY_AT_AURI_PATTERNS = [
        "enfocate", "enfócate", "respondé bien", "responde bien",
        "eso no viene al caso",
        "dejá de decir tonteras", "deja de decir tonteras",
        "dejá de decir estupideces", "deja de decir estupideces",
        "no estás ayudando", "no estas ayudando",
        "no servís", "no sirves",
    ]

    # Referencias genéricas a Auri / asistente
    ANGRY_AT_AURI_REFERENCES = [
        "auri", "asistente", "vos", "usted", "tu", "tú",
    ]

    # Expresiones fuertes culturales pero no necesariamente ataque directo
    CULTURAL_STRONG_MARKERS = [
        "no mames", "no mame", "concha de tu madre", "la concha de tu madre",
        "verga", "hijueputa", "hp ", "gonorrea",
    ]

    # Términos que NUNCA debe usar Auri (ni aunque el usuario los use)
    ABSOLUTE_FORBIDDEN_TERMS = [
        "hijo de puta", "hijueputa", "hp ", "maricón", "maricon",
        "pendejo", "pendeja", "imbécil", "imbecil",
    ]

    # -----------------------------
    # Helpers internos
    # -----------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _contains_any(text: str, patterns: List[str]) -> bool:
        return any(p in text for p in patterns)

    @staticmethod
    def _count_any(text: str, patterns: List[str]) -> int:
        return sum(1 for p in patterns if p in text)

    # -----------------------------
    # Perfil de jerga
    # -----------------------------

    @staticmethod
    def ensure_slang_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Garantiza que slang_profile tenga estructura mínima.

        Estructura recomendada:
        {
            "detected_country": Optional[str],
            "country_scores": Dict[str, float],
            "samples_seen": int,
            "use_slang_outbound": bool,
            "allow_humor": bool,
            "force_serious": bool,
            "last_modes": List[str],
            "last_updated": float,
        }
        """
        if profile is None:
            profile = {}

        profile.setdefault("detected_country", None)
        profile.setdefault("country_scores", {})
        profile.setdefault("samples_seen", 0)
        profile.setdefault("use_slang_outbound", False)
        profile.setdefault("allow_humor", True)
        profile.setdefault("force_serious", False)
        profile.setdefault("last_modes", [])
        profile.setdefault("last_updated", time.time())

        # Inicializar scores
        for country in SlangModeEngine.COUNTRY_SLANG.keys():
            profile["country_scores"].setdefault(country, 0.0)

        return profile

    def _update_country_scores(self, norm: str, profile: Dict[str, Any]) -> None:
        scores = profile["country_scores"]

        for country, slang_list in self.COUNTRY_SLANG.items():
            hits = self._count_any(norm, slang_list)
            if hits > 0:
                scores[country] += hits * 1.0

        profile["samples_seen"] += 1
        total_score = sum(scores.values())
        if total_score <= 0:
            return

        best_country = max(scores, key=lambda c: scores[c])
        best_score = scores[best_country]
        confidence = best_score / (total_score + 1e-6)

        # Se necesita algo de confianza y muestras
        if confidence >= 0.45 and profile["samples_seen"] >= 3:
            profile["detected_country"] = best_country
            profile["use_slang_outbound"] = True

        profile["last_updated"] = time.time()

    def _classify_mode(self, norm: str) -> Optional[str]:
        """
        Devuelve uno de:
          - "friendly_slang"
          - "frustrated"
          - "angry_at_auri"
          - "cultural_strong"
          - None
        """
        has_friendly = self._contains_any(norm, self.FRIENDLY_MARKERS)
        has_frustration = self._contains_any(norm, self.FRUSTRATION_MARKERS)
        has_cultural_strong = self._contains_any(norm, self.CULTURAL_STRONG_MARKERS)
        has_vulgar = self._contains_any(norm, self.UNIVERSAL_BAD)
        has_auri_ref = self._contains_any(norm, self.ANGRY_AT_AURI_REFERENCES) or "auri" in norm
        regano_directo = self._contains_any(norm, self.ANGRY_AT_AURI_PATTERNS)
        has_troll = self._contains_any(norm, self.TROLL_TRIGGERS)

        # Señales para país / jerga en general
        has_any_slang = any(
            self._contains_any(norm, slang_list)
            for slang_list in self.COUNTRY_SLANG.values()
        )

        # 1) Regaño directo hacia Auri
        if regano_directo or ((has_frustration or has_vulgar) and has_auri_ref):
            return "angry_at_auri"

        # 2) Frustración general (con o sin vulgar)
        if has_frustration or has_vulgar:
            return "frustrated"

        # 3) Expresión fuerte cultural
        if has_cultural_strong:
            return "cultural_strong"

        # 4) Broma / jerga amistosa / trolling suave
        if has_troll or has_friendly or has_any_slang:
            return "friendly_slang"

        return None

    # -----------------------------------------------------------
    # API PRINCIPAL
    # -----------------------------------------------------------

    def detect(
        self,
        text: str,
        slang_profile: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Detecta el tipo de jerga / actitud emocional aproximada en el texto
        y ACTUALIZA slang_profile adaptativamente.

        Devuelve:
        - "friendly_slang"
        - "frustrated"
        - "angry_at_auri"
        - "cultural_strong"
        - None
        """
        if not text or not text.strip():
            return None

        slang_profile = self.ensure_slang_profile(slang_profile)
        norm = self._normalize(text)

        # 1) Actualizar país según jerga
        self._update_country_scores(norm, slang_profile)

        # 2) Clasificar modo
        mode = self._classify_mode(norm)

        # Guardar historial
        if mode:
            slang_profile["last_modes"].append(mode)
            slang_profile["last_modes"] = slang_profile["last_modes"][-10:]

        # Flags emocionales básicos según modo
        if mode in ("frustrated", "angry_at_auri"):
            slang_profile["allow_humor"] = False
            slang_profile["force_serious"] = True
        elif mode == "friendly_slang":
            # Solo permitir humor si no hay un force_serious externo (EmotionLayer)
            if not slang_profile.get("force_serious"):
                slang_profile["allow_humor"] = True

        slang_profile["last_updated"] = time.time()
        return mode

    # -----------------------------------------------------------
    # RESPUESTAS SEGÚN MODO
    # -----------------------------------------------------------

    def respond(
        self,
        mode: Optional[str],
        slang_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera una respuesta corta basada en:
        - mode (friendly_slang, frustrated, angry_at_auri, cultural_strong, None)
        - slang_profile (país detectado, flags de humor/seriedad)

        Nunca usa insultos ni términos prohibidos.
        """
        slang_profile = self.ensure_slang_profile(slang_profile)
        detected_country: Optional[str] = slang_profile.get("detected_country")
        use_slang = bool(slang_profile.get("use_slang_outbound"))
        allow_humor = bool(slang_profile.get("allow_humor"))
        force_serious = bool(slang_profile.get("force_serious"))

        # Map de jerga suave por país (solo cosas amables)
        friendly_word_by_country = {
            "tico": "mae",
            "mex": "wey",
            "arg": "che",
            "per": "causa",
            "col": "parce",
            "chi": "weon",
            "ven": "pana",
            "dom": "manín",
            "es-es": "tío",
        }

        friendly_word = friendly_word_by_country.get(detected_country or "", "")

        # Seguridad extra: evitar palabras dudosas
        if friendly_word and any(
            fw in friendly_word
            for fw in ["gonorrea", "culiao", "hp", "playo", "verga"]
        ):
            friendly_word = ""

        # Helpers internos de respuesta
        def serious_ack() -> str:
            return "Ok, voy a ponerme más serio y preciso con lo que te respondo."

        def frustrated_ack() -> str:
            if force_serious or not allow_humor:
                return "Veo que esto te está frustrando, voy a ajustar mis respuestas para ayudarte mejor."
            if use_slang and friendly_word:
                return f"Uf, entiendo la vara {friendly_word}, voy a afinar mis respuestas para que sí te sirvan."
            return "Entiendo que te frustra, voy a afinar mis respuestas para que sean más útiles."

        def angry_at_auri_ack() -> str:
            # Siempre serio, sin humor ni jerga
            return (
                "Perdón si no te he respondido como necesitabas. "
                "A partir de ahora voy a ser más directo y preciso contigo."
            )

        def friendly_slang_ack() -> str:
            if force_serious:
                return "Perfecto, sigo atento a lo que necesites."
            if use_slang and allow_humor and friendly_word:
                return f"Jajaja, entendido {friendly_word}, sigo aquí para lo que ocupés."
            if allow_humor:
                return "Jajaja, entendido, sigo aquí pendiente de lo que necesites."
            return "Entendido, sigo pendiente de lo que necesites."

        def cultural_strong_ack() -> str:
            if force_serious or not allow_humor:
                return "Capto lo que dices, voy a responderte de forma más clara y directa."
            if use_slang and friendly_word:
                return f"Capto la idea {friendly_word}, voy a responderte más claro."
            return "Capto la idea, voy a responderte más claro."

        # Selección según modo
        if mode is None:
            return (
                "Entendido, voy a tomar eso en cuenta 🟣"
                if (allow_humor and not force_serious)
                else "Entendido, lo tomo en cuenta."
            )

        if mode == "angry_at_auri":
            return angry_at_auri_ack()

        if mode == "frustrated":
            return frustrated_ack()

        if mode == "friendly_slang":
            return friendly_slang_ack()

        if mode == "cultural_strong":
            return cultural_strong_ack()

        # Fallback seguro
        return serious_ack()
