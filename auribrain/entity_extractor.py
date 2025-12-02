# auribrain/entity_extractor.py

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from openai import OpenAI


@dataclass
class ExtractedReminder:
    title: str
    datetime: Optional[datetime]
    kind: str
    repeats: str


class EntityExtractor:
    """
    EntityExtractor V3 (limpio, corregido)

    Se encarga EXCLUSIVAMENTE de extraer RECORDATORIOS.

    Soporta:
    - tiempos relativos: "en 5 minutos", "en 2 horas"
    - fechas relativas: "mañana", "pasado mañana", "esta noche"
    - días de la semana: "el viernes a las 3"
    - repeticiones: diario / semanal / mensual
    - categorías: payment / birthday / class / event / generic

    Devuelve SIEMPRE un JSON VÁLIDO como:
    {
        "title": "...",
        "datetime": "2025-12-04T09:00:00",
        "kind": "payment",
        "repeats": "once"
    }
    """

    def __init__(self):
        self.client = OpenAI()

    def _clean_json_text(self, raw: str) -> str:
        raw = raw.strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return raw

    def extract_reminder(
        self,
        text: str,
        now: Optional[datetime] = None
    ) -> Optional[ExtractedReminder]:

        now = now or datetime.now()
        now_iso = now.isoformat()
        now_date = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M")

        prompt = f"""
Eres un extractor especializado en RECORDATORIOS para un asistente llamado Auri.

DEBES devolver SOLO un objeto JSON válido con los campos:

{{
  "title": "título limpio",
  "datetime": "YYYY-MM-DDTHH:MM:SS" o null,
  "kind": "payment | birthday | class | event | generic",
  "repeats": "once | daily | weekly | monthly"
}}

REGLAS:

1) Tiempos relativos:
   "en 5 minutos" → now + 5 minutos
   "en 2 horas" → now + 2 horas
   "en X días" → now + X días

2) Fechas relativas:
   "mañana" → siguiente día 09:00
   "pasado mañana" → +2 días 09:00
   "esta noche" → hoy 20:00
   "esta tarde" → hoy 15:00
   "esta mañana" → hoy 09:00

3) Día de la semana:
   "el viernes" → próximo viernes 09:00
   "el lunes a las 3" → próximo lunes 15:00

4) Hora:
   Si el usuario da hora → respeta esa hora.
   Si solo da fecha → usa 09:00.
   Si no da nada → datetime = null

5) Repeticiones:
   "todos los días" → daily
   "cada semana" → weekly
   "cada mes" → monthly
   Si no menciona repetición → once

6) Categorías:
   Pagos → payment
   Cumpleaños → birthday
   Clases → class
   Eventos → event
   Otros → generic

7) BORRADOS:
   Si el mensaje contiene "borra", "elimina", etc. → no cambies el título.
   El motor de acciones decide si es delete o create.

8) FORMATO OBLIGATORIO:
   Devuelve SOLO JSON.
   NO incluyas explicaciones.
   NO incluyas texto fuera del JSON.

CONTEXTO DE TIEMPO:
- now_iso: {now_iso}
- now_date: {now_date}
- now_time: {now_time}

MENSAJE DEL USUARIO:
\"\"\"{text}\"\"\"
"""

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "Devuelve SOLO un objeto JSON válido. Sin explicación."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            raw = resp.choices[0].message.content or ""
            raw = self._clean_json_text(raw)
            obj = json.loads(raw)

            title = (obj.get("title") or "").strip()
            if not title:
                return None

            # DATETIME
            dt_str = obj.get("datetime")
            dt_obj = None
            if dt_str:
                dt_obj = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=obj.get("kind", "generic"),
                repeats=obj.get("repeats", "once")
            )

        except Exception as e:
            print(f"[EntityExtractor] ERROR CRÍTICO: {e}")
            return None
