# auribrain/fact_extractor.py

import os
import json
from datetime import datetime
from openai import OpenAI

client = OpenAI()

FACT_SYSTEM = """
Eres un extractor de HECHOS personales del usuario.
Tu tarea es leer el mensaje y devolver SOLO hechos importantes.

Formato:
{
  "facts": [
    {
      "text": "frase corta",
      "category": "relationship | preferences | work | health | finance | life | goal | other",
      "importance": 1-5,
      "confidence": 0.0-1.0
    }
  ]
}

Reglas:
- No inventes nada.
- Si no hay hechos importantes: devuelve { "facts": [] }.
- Usa enunciados cortos, neutrales y útiles.
- No repitas hechos obvios ni vagos.
"""

def extract_facts(message: str):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FACT_SYSTEM},
                {"role": "user", "content": message},
            ],
        )

        raw = res.choices[0].message.content or "{}"
        data = json.loads(raw)
        return data.get("facts", [])

    except Exception as e:
        print(f"[FactExtractor] ERROR: {e}")
        return []
