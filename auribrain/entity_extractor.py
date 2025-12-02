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

        now = now or datetime.now()
        now_iso = now.isoformat()

        prompt = f"""
Eres un extractor de entidades de recordatorios para un asistente llamado Auri.

El usuario habla en español.

Transforma el mensaje en un JSON válido con:

- title: titulo limpio
- datetime: ISO8601 o null
- kind: payment|birthday|class|event|generic
- repeats: once|daily|weekly|monthly

Reglas especiales:
- “en 5 minutos” → now + 5 min
- “mañana” → mañana 09:00
- “pasado mañana” → +2 días 09:00
- “esta noche” → 20:00
- “esta tarde” → 15:00
- “lunes / martes / etc” → próximo día
- Si no hay hora → 09:00
- “todos los días” → daily
- “cada semana” → weekly
- “cada mes” → monthly

NOW = {now_iso}

Ejemplo correcto:
{{
 "title": "tarea de matemáticas",
 "datetime": "2025-12-03T09:00:00",
 "kind": "event",
 "repeats": "once"
}}

Mensaje:
{text}
"""

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {"role": "system", "content": "Devuelve SOLO JSON válido."},
                    {"role": "user", "content": prompt},
                ]
            )

            raw = resp.choices[0].message.content
            obj = json.loads(raw)

            title = obj.get("title", "").strip()
            if not title:
                return None

            dt_str = obj.get("datetime")
            dt_obj = None
            if dt_str:
                dt_obj = datetime.fromisoformat(dt_str)

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=obj.get("kind", "generic"),
                repeats=obj.get("repeats", "once"),
            )

        except Exception as e:
            print(f"[EntityExtractor] ERROR CRÍTICO: {e}")
            return None
