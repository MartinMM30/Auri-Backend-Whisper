# auribrain/fact_extractor.py

import json
from openai import OpenAI


def extract_facts(text: str):
    """
    FactExtractor V4 – estable y compatible con response_format=json_object
    """

    client = OpenAI()

    system_msg = (
        "Eres un extractor de HECHOS del usuario. "
        "Debes devolver un objeto JSON válido. "
        "La palabra 'json' ya fue mencionada. "
        "Tu salida DEBE ser estrictamente un json_object."
    )

    user_prompt = f"""
Extrae *hechos personales del usuario* a partir del siguiente texto.

Regresa SIEMPRE un JSON con la forma:

{{
  "facts": [
    {{
      "text": "hecho detectado",
      "category": "relationship | preference | personal | pet | work | other",
      "importance": 1,
      "confidence": 1.0
    }}
  ]
}}

Reglas:
- Si NO hay hechos, devuelve "facts": [].
- No inventes nada.
- Un hecho es información sobre el usuario, familia, gustos, mascotas, preferencias, etc.
- Usa importance de 1 a 5 según relevancia.
- Usa confidence entre 0.0 y 1.0.

TEXTO DEL USUARIO:
\"\"\"{text}\"\"\"
"""

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw = resp.output_text
        data = json.loads(raw)

        if "facts" not in data:
            return []

        return data["facts"]

    except Exception as e:
        print("[FactExtractor ERROR]", e)
        return []
