# auribrain/entity_extractor.py

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from openai import OpenAI


@dataclass
class ExtractedReminder:
    title: str
    datetime: Optional[datetime]
    kind: str
    repeats: str


class EntityExtractor:

    def __init__(self):
        self.client = OpenAI()

    def extract_reminder(self, text: str, now: Optional[datetime] = None) -> Optional[ExtractedReminder]:
        now = now or datetime.utcnow()
        now_iso = now.iso8601()

        prompt = f"""
Eres un extractor de entidades. 
Devuelve SIEMPRE un JSON VÁLIDO.

Instrucciones:
- title: título del recordatorio, texto limpio
- datetime: fecha en ISO 8601 o null
- kind: payment, birthday, class, event, generic
- repeats: once, daily, weekly, monthly
- Si el usuario dice "borrar", "quita", NO cambies el título.
- Si no hay fecha → datetime = null
- Hora default: 09:00

Ejemplo correcto:
{{
 "title": "pago de agua",
 "datetime": "2025-12-04T09:00:00",
 "kind": "payment",
 "repeats": "once"
}}

Mensaje:
\"\"\"{text}\"\"\"
"""

        try:
            # JSON MODE — esto arregla TODO
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                input=[
                    {"role": "system", "content": "Eres un extractor de entidades, responde SOLO JSON válido."},
                    {"role": "user", "content": prompt},
                ],
            )

            data = resp.output[0].content[0].text
            obj = json.loads(data)

            title = obj.get("title", "").strip()
            if not title:
                return None

            dt_str = obj.get("datetime")
            dt_obj = None
            if dt_str:
                dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=obj.get("kind", "generic"),
                repeats=obj.get("repeats", "once"),
            )

        except Exception as e:
            print(f"[EntityExtractor] ERROR CRÍTICO: {e}")
            return None
