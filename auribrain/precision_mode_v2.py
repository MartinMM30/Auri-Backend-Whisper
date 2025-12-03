# auribrain/precision_mode_v2.py

from __future__ import annotations
from typing import Dict, Any
import re


class PrecisionModeV2:
    """
    PrecisionMode V2 — Modo técnico / factual ultra conciso.

    Detecta cuando el usuario quiere:
      - Definiciones
      - Explicaciones
      - Traducciones
      - Código
      - Procedimientos directos
      - Datos concretos ("quiero que me digas el nombre de...")

    Cuando se activa:
      - Humor OFF
      - Emojis OFF
      - Jerga OFF
      - Tono emocional OFF
      - Se fuerza precisión y brevedad
    """

    TRIGGERS = [
        # Definiciones / significado
        r"\bqué es\b", r"\bque es\b",
        r"\bqué significa\b", r"\bque significa\b",
        r"\bqué sería\b", r"\bque seria\b",

        # Cómo hacer / pasos
        r"\bcomo hago\b", r"\bcómo hago\b",
        r"\bpasos para\b",

        # Traducciones
        r"\bcomo se dice\b", r"\bcómo se dice\b",
        r"\btraduce\b", r"\btraducción\b",

        # Explicar
        r"\bexplicame\b", r"\bexplícame\b",
        r"\benséñame\b", r"\benseñame\b",

        # Programación / código
        r"\bcódigo\b", r"\bcode\b",
        r"\bpython\b", r"\bflutter\b", r"\bapi\b",

        # Peticiones de información directa
        r"\bquiero saber\b",
        r"\bquiero que me digas\b",
        r"\bquiero que me digas el nombre\b",
        r"\bdime el nombre de\b",
        r"\bdime cómo se llama\b", r"\bdime como se llama\b",
        r"\bdime quién es\b", r"\bdime quien es\b",
    ]

    def __init__(self):
        pass

    # -------------------------------------------------------------
    # Detecta si el usuario quiere modo técnico / factual
    # -------------------------------------------------------------
    def detect(self, text: str) -> bool:
        norm = text.lower()
        for pattern in self.TRIGGERS:
            if re.search(pattern, norm):
                return True
        return False

    # -------------------------------------------------------------
    # Cambia el comportamiento del motor usando slang_profile
    # -------------------------------------------------------------
    def apply(self, slang_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuerza modo técnico en Auri.
        Devuelve instrucción para el LLM:

        {
            "force_serious": True,
            "allow_humor": False,
            "precision_mode": True,
            "llm_style": "technical_concise"
        }
        """

        slang_profile["force_serious"] = True
        slang_profile["allow_humor"] = False
        slang_profile["use_slang_outbound"] = False

        return {
            "force_serious": True,
            "allow_humor": False,
            "precision_mode": True,
            "llm_style": "technical_concise",
        }
