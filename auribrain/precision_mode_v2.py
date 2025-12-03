# auribrain/precision_mode_v2.py

from __future__ import annotations
from typing import Optional, Dict, Any
import re


class PrecisionModeV2:
    """
    PrecisionMode V2 — Modo técnico ultra conciso.

    Este módulo detecta cuándo el usuario quiere una respuesta:
      - Definición
      - Explicación
      - Traducción
      - Código
      - Procedimiento directo

    Cuando se activa:
      - Humor OFF
      - Emojis OFF
      - Jerga OFF
      - Tono emocional OFF
      - Se fuerza precisión y brevedad

    API:
      detect(text: str) -> bool
      apply(slang_profile: dict) -> dict
    """

    TRIGGERS = [
        r"\bqué es\b", r"\bque es\b",
        r"\bqué significa\b", r"\bque significa\b",
        r"\bcomo hago\b", r"\bcómo hago\b",
        r"\bcomo se dice\b", r"\bcómo se dice\b",
        r"\btraduce\b", r"\btraducción\b",
        r"\bexplicame\b", r"\bexplícame\b",
        r"\bcomo decir\b", r"\bcómo decir\b",
        r"\benséñame\b", r"\benseñame\b",
        r"\bcódigo\b", r"\bcode\b",
        r"\bpython\b", r"\bflutter\b", r"\bapi\b",
        r"\bqué sería\b", r"\bque seria\b",
        r"\bpasos para\b",
    ]

    def __init__(self):
        pass

    # -------------------------------------------------------------
    # Detecta si el usuario quiere modo técnico
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
