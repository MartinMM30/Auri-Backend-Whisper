# auribrain/fact_extractor.py

import json
from openai import OpenAI


def extract_facts(text: str):
    """
    FactExtractor V5 – Compatible con OpenAI Responses API (sin response_format)
    Produce SIEMPRE JSON parseable mediante instrucción en el prompt.
    """

    client = OpenAI()

    system_msg = (
        "Eres un extractor de hechos personales del usuario. "
        "Debes devolver EXCLUSIVAMENTE un JSON válido. "
        "No incluyas explicaciones, solo JSON."
    )

    user_prompt = f"""
Extrae hechos personales del usuario.

Devuelve SIEMPRE este formato JSON:

{{
  "facts": [
    {{
      "text": "hecho",
      "category": "relationship | preference | personal | pet | work | other",
      "importance": 1,
      "confidence": 1.0
    }}
  ]
}}

Reglas:
- Si no hay hechos, devuelve "facts": [].
- No inventes nada.
- Un hecho es información sobre familia, gustos, mascotas, trabajo, nombre, etc.

TEXTO:
\"\"\"{text}\"\"\"
"""

    try:
        # 🚀 API nueva de OpenAI
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw = resp.output_text.strip()

        # Intentar parsear el JSON generado
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("[FactExtractor] WARNING: El modelo devolvió algo no parseable")
            print(raw)
            return []

        facts = data.get("facts", [])
        return facts

    except Exception as e:
        print("[FactExtractor ERROR]", e)
        return []
