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
  kind: str            # "payment", "birthday", "class", "generic", etc.
  repeats: str         # "once", "daily", "weekly", etc.


class EntityExtractor:
  """
  Usa OpenAI para extraer entidades de lenguaje natural:
  - título del recordatorio
  - fecha/hora ISO
  - tipo (pago, cumpleaños, clase…)
  - repetición
  """

  def __init__(self):
    self.client = OpenAI()

  def extract_reminder(self, text: str, now: Optional[datetime] = None) -> Optional[ExtractedReminder]:
    now = now or datetime.utcnow()
    now_iso = now.isoformat()

    prompt = f"""
Quiero que extraigas la información estructurada de un pedido de recordatorio.

Devuélveme EXCLUSIVAMENTE un JSON válido (sin explicaciones, sin texto extra) con la forma:

{{
  "title": "string, título corto del recordatorio",
  "datetime": "string ISO 8601 con fecha y hora completas, o null si no está claro",
  "kind": "payment | birthday | class | event | generic",
  "repeats": "once | daily | weekly | monthly"
}}

Reglas:
- El texto está en español.
- Usa la fecha/hora actual como referencia: "{now_iso}".
- Si dice "mañana", "pasado mañana", "el viernes", etc., conviértelo a una fecha concreta.
- Si no hay hora explícita, usa una hora razonable: 09:00.
- Si es algo como "cada lunes", usa "weekly".
- Si es un pago ("luz", "agua", "internet", "renta", etc.), usa kind = "payment".
- Si menciona cumpleaños, usa kind = "birthday".
- Si no estás seguro, usa kind = "generic".
- Si no puedes determinar ninguna fecha, pon "datetime": null pero igual llena "title".

Mensaje del usuario:
\"\"\"{text}\"\"\""""

    try:
      resp = self.client.responses.create(
        model="gpt-4o-mini",
        input=[
          {"role": "system", "content": "Eres un extractor de entidades que responde SOLO JSON válido."},
          {"role": "user", "content": prompt},
        ],
      )

      raw = (resp.output_text or "").strip()
      data = json.loads(raw)

      title = str(data.get("title") or "").strip()
      if not title:
        return None

      dt_str = data.get("datetime")
      dt_obj: Optional[datetime] = None
      if isinstance(dt_str, str) and dt_str.strip():
        try:
          dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
          dt_obj = None

      kind = str(data.get("kind") or "generic").strip()
      repeats = str(data.get("repeats") or "once").strip()

      return ExtractedReminder(
        title=title,
        datetime=dt_obj,
        kind=kind,
        repeats=repeats,
      )

    except Exception as e:
      print(f"[EntityExtractor] Error extrayendo recordatorio: {e}")
      return None
