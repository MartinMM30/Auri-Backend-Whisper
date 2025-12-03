# auribrain/emotion_smartlayer_v3.py

from __future__ import annotations
from typing import Dict, Any, Optional
import re


class EmotionSmartLayerV3:
    """
    Emotion SmartLayer V3 — Regulador emocional inteligente para AuriMind.

    Funciones principales:
    - Tomar la emoción global del usuario (overall, stress, energy, affection).
    - Ajustar humor, seriedad y cercanía.
    - Detectar regaños directos hacia Auri → modo serio obligado.
    - Activar contención suave cuando hay tristeza.
    - Activar motivación cuando hay energía alta.
    - Activar tono técnico cuando el usuario está concentrado.
    - Modular flags del slang_profile:
        slang_profile["allow_humor"]
        slang_profile["force_serious"]
    """

    REGAÑO_PATTERNS = [
        r"\b(enfocate|enfócate)\b",
        r"\brespond(e|é) bien\b",
        r"\bdej(a|á) de decir tonteras\b",
        r"\bdej(a|á) de decir estupideces\b",
        r"\bno est(a|á)s ayudando\b",
        r"\bno serv(i|í)s\b",
        r"\best(o|a) no viene al caso\b",
    ]

    TECH_MODE_TRIGGERS = [
        "explicame", "explícame", "cómo hago", "como hago",
        "qué es", "que es", "cómo funciona", "como funciona",
        "código", "code", "programación", "api", "flutter", "python",
    ]

    def __init__(self):
        pass

    # -------------------------------------------------------------
    # Detecta si el usuario regaña directamente a Auri
    # -------------------------------------------------------------
    def _is_user_scolding(self, text: str) -> bool:
        norm = text.lower()
        for p in self.REGAÑO_PATTERNS:
            if re.search(p, norm):
                return True
        return False

    # -------------------------------------------------------------
    # Detecta intención técnica (al usuario le importa la exactitud)
    # -------------------------------------------------------------
    def _detect_tech_mode(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.TECH_MODE_TRIGGERS)

    # -------------------------------------------------------------
    # APLICAR MODOS EMOCIONALES
    # -------------------------------------------------------------
    def apply(
        self,
        text: str,
        emotion_snapshot: Dict[str, Any],
        slang_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analiza emoción + texto y ajusta flags internos.
        Devuelve un dict con sugerencias para AuriMind:

        {
            "force_serious": bool,
            "allow_humor": bool,
            "emotional_tone": "soft|neutral|motivational|contained|technical",
        }
        """

        norm = text.lower()

        overall = emotion_snapshot.get("overall", "neutral")
        stress = float(emotion_snapshot.get("stress", 0.2))
        energy = float(emotion_snapshot.get("energy", 0.5))
        affection = float(emotion_snapshot.get("affection", 0.4))

        # -------------------------
        # resultado final
        # -------------------------
        result = {
            "force_serious": slang_profile.get("force_serious", False),
            "allow_humor": slang_profile.get("allow_humor", True),
            "emotional_tone": "neutral",
        }

        # -------------------------
        # 1) Regaño hacia Auri
        # -------------------------
        if self._is_user_scolding(norm):
            result["force_serious"] = True
            result["allow_humor"] = False
            result["emotional_tone"] = "serious"
            slang_profile["force_serious"] = True
            slang_profile["allow_humor"] = False
            return result

        # -------------------------
        # 2) Estrés alto → contención
        # -------------------------
        if stress >= 0.65:
            result["force_serious"] = True
            result["allow_humor"] = False
            result["emotional_tone"] = "contained"  # tono suave, calmado
            slang_profile["allow_humor"] = False
            return result

        # -------------------------
        # 3) Tristeza o “overall” negativo → apoyo suave
        # -------------------------
        if overall in ("sad", "low", "tired"):
            result["allow_humor"] = False
            result["emotional_tone"] = "soft"
            return result

        # -------------------------
        # 4) Mucho afecto → Auri más cariñosa
        # -------------------------
        if affection >= 0.75:
            result["emotional_tone"] = "soft"
            # humor permitido si no hay estrés
            result["allow_humor"] = stress < 0.45

        # -------------------------
        # 5) Energía alta → motivación
        # -------------------------
        if energy >= 0.75:
            result["emotional_tone"] = "motivational"

        # -------------------------
        # 6) Usuario en “modo técnico”
        # -------------------------
        if self._detect_tech_mode(norm):
            result["force_serious"] = True
            result["allow_humor"] = False
            result["emotional_tone"] = "technical"
            slang_profile["force_serious"] = True
            slang_profile["allow_humor"] = False

        # -------------------------
        # 7) Ajustar slang_profile final
        # -------------------------
        slang_profile["force_serious"] = result["force_serious"]
        slang_profile["allow_humor"] = result["allow_humor"]

        return result
