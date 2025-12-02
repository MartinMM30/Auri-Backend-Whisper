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
    """
    EntityExtractor V3

    - Usa 'now' como referencia para tiempos relativos.
    - Soporta:
        - "en 5 minutos", "dentro de 2 horas"
        - "mañana", "pasado mañana", "esta noche", "esta tarde"
        - días de la semana: "el viernes", "el lunes a las 3"
        - repetición: diario / semanal / mensual
    - Devuelve SIEMPRE JSON válido (el modelo lo genera).
    """

    def __init__(self):
        self.client = OpenAI()

    def _clean_json_text(self, raw: str) -> str:
        """
        A veces el modelo mete ```json ... ``` o texto extra.
        Limpiamos para quedarnos SOLO con el JSON.
        """
        raw = raw.strip()

        # Quitar fences ```json ... ```
        if raw.startswith("```"):
            raw = raw.strip("`")
            # puede venir "json\n{...}"
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
Eres un extractor de entidades de recordatorios para un asistente llamado Auri.
El usuario habla en español.

TRANSFORMA el mensaje del usuario en un JSON **VÁLIDO** con:

- title: título corto y limpio (sin "recuérdame", "pon un recordatorio", etc.)
- datetime: fecha y hora completa en formato ISO 8601 "YYYY-MM-DDTHH:MM:SS"
           o null si el usuario NO dio suficiente información de tiempo.
- kind: uno de ["payment", "birthday", "class", "event", "generic"]
- repeats: uno de ["once", "daily", "weekly", "monthly"]

CONTEXTO DE TIEMPO (NOW) – hora local del usuario:
- now_iso: {now_iso}
- now_date: {now_date}
- now_time: {now_time}

REGLAS IMPORTANTES:

1) Tiempos relativos:
   - "en 5 minutos" → now + 5 minutos
   - "en 10 min" → now + 10 minutos
   - "dentro de media hora" → now + 30 minutos
   - "dentro de 2 horas" → now + 2 horas
   - "en una hora" → now + 1 hora
   - "en X días" → now + X días

2) Fechas relativas:
   - "mañana" → día siguiente, hora por defecto 09:00 si no se especifica otra.
   - "pasado mañana" → now + 2 días, hora por defecto 09:00.
   - "esta noche" → hoy a las 20:00 (si ya pasó, usar el día siguiente a las 20:00).
   - "esta tarde" → hoy a las 15:00.
   - "esta mañana" → hoy a las 09:00.

3) Días de la semana:
   - "el lunes", "el martes", etc. → usar el PRÓXIMO día con ese nombre.
   - Si da hora ("el viernes a las 3") → usar esa hora.
   - Si dice "3 de la tarde" → 15:00.

4) Hora:
   - Si el usuario da hora ("a las 7", "a las 19:30") → respeta esa hora.
   - Si solo da fecha ("el 5 de diciembre") sin hora → usar 09:00.
   - Si NO da hora ni fecha → datetime = null.

5) Repeticiones:
   - "todos los días", "cada día" → "daily"
   - "cada semana", "todos los lunes" → "weekly"
   - "cada mes", "todos los meses", "cada 7 de mes" → "monthly"
   - Si no se menciona repetición → "once".

6) kind:
   - Si se refiere a pagos (agua, luz, renta, alquiler, internet, teléfono, recibo,
     factura, tarjeta, crédito, banco) → "payment".
   - Si es cumpleaños (cumple, cumpleaños, birthday) → "birthday".
   - Si es clase, curso, lección, universidad, materia → "class".
   - Si es evento puntual (reunión, cita, médico, doctor, llamada, entrevista) → "event".
   - En otro caso → "generic".

7) BORRAR / QUITAR:
   - Si el mensaje contiene "borra", "borrar", "quita", "quitar", "elimina", "eliminar",
     NO modifiques el significado del título, solo límpialo (sin "el recordatorio de").
   - El motor de acciones decide si es delete o create. Tú SOLO devuelves el título.

8) FORMATO DE SALIDA:
   - Responde SOLO un JSON válido, sin texto adicional.
   - Ejemplo de salida correcta:

   {{
     "title": "pago de agua",
     "datetime": "2025-12-04T09:00:00",
     "kind": "payment",
     "repeats": "once"
   }}

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
                        "content": "Devuelve SOLO JSON válido, sin explicación adicional."
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

            dt_str = obj.get("datetime")
            dt_obj: Optional[datetime] = None
            if dt_str:
                # soportar posible sufijo "Z"
                dt_obj = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))

            kind = (obj.get("kind") or "generic").strip() or "generic"
            repeats = (obj.get("repeats") or "once").strip() or "once"

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=kind,
                repeats=repeats,
            )

        except Exception as e:
            print(f"[EntityExtractor V3] ERROR CRÍTICO: {e}")
            return None
        
