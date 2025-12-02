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
    EntityExtractor V2
    - Soporta tiempos relativos: "en 5 minutos", "dentro de 2 horas"
    - Soporta expresiones: "mañana", "pasado mañana", "esta noche", "esta tarde"
    - Soporta días de la semana: "el viernes", "el lunes a las 3"
    - Devuelve SIEMPRE JSON válido con:
        - title: texto corto y limpio
        - datetime: ISO 8601 o null
        - kind: payment | birthday | class | event | generic
        - repeats: once | daily | weekly | monthly
    """

    def __init__(self):
        self.client = OpenAI()

    def extract_reminder(
        self,
        text: str,
        now: Optional[datetime] = None
    ) -> Optional[ExtractedReminder]:
        """
        text: frase del usuario (ej: "recuérdame comer en 5 minutos")
        now:  fecha/hora de referencia (ya viene de ActionsEngine)
        """

        # Usamos NOW como referencia para tiempos relativos
        now = now or datetime.now()
        now_iso = now.isoformat()  # 🔥 FIX: isoformat(), no iso8601()
        now_date = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M")

        prompt = f"""
Eres un extractor de entidades para un asistente de voz llamado Auri.
Tu tarea es transformar el mensaje del usuario en un JSON **válido** con:

- title: título del recordatorio, corto y limpio (sin "recuérdame", "pon un recordatorio", etc.)
- datetime: fecha y hora completa en formato ISO 8601 ("YYYY-MM-DDTHH:MM:SS")
           o null si el usuario NO dió suficiente información de tiempo.
- kind: uno de ["payment", "birthday", "class", "event", "generic"]
- repeats: uno de ["once", "daily", "weekly", "monthly"]

IMPORTANTE:
- El usuario habla en español.
- Usa SIEMPRE la fecha/hora de referencia NOW para interpretar tiempos relativos.

NOW (fecha/hora de referencia del usuario):
- now_iso: {now_iso}
- now_date: {now_date}
- now_time: {now_time}

REGLAS DE INTERPRETACIÓN:

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
   - Si además da hora ("el viernes a las 3") → usar esa hora (03:00) en formato 24h o inferir si dice "3 de la tarde" → 15:00.

4) Hora:
   - Si el usuario da una hora concreta ("a las 7", "a las 19:30") → respeta esa hora.
   - Si solo dice fecha ("el 5 de diciembre") sin hora → usar 09:00.
   - Si NO da hora ni fecha → datetime = null.

5) Repeticiones (repeats):
   - "cada día", "todos los días" → "daily"
   - "cada semana", "todos los lunes" → "weekly"
   - "cada mes", "todos los meses", "cada 7 de mes" → "monthly"
   - Si no se menciona repetición → "once".

6) kind:
   - Si el título se refiere a pagos (agua, luz, renta, alquiler, internet, teléfono, recibo, factura, tarjeta, crédito, banco) → "payment".
   - Si es cumpleaños (cumple, cumpleaños, birthday) → "birthday".
   - Si es clase, curso, lección, universidad, materia → "class".
   - Si parece un evento puntual (reunión, cita, evento, médico, doctor, llamada, entrevista) → "event".
   - En otro caso → "generic".

7) BORRAR / QUITAR:
   - Si el mensaje contiene "borra", "borrar", "quita", "quitar", "elimina", "eliminar",
     NO transformes el título, solo hazlo limpio (sin "el recordatorio de").
   - El ActionsEngine decide si es delete o create, tú SOLO devuelves el título.

8) Formato de salida:
   - Responde SIEMPRE un JSON VÁLIDO, sin comentarios, sin texto extra.
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
            # JSON MODE — respuesta SIEMPRE en JSON
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                input=[
                    {
                        "role": "system",
                        "content": "Eres un extractor de entidades de recordatorios. Responde SOLO JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )

            # Dependiendo de la versión del SDK, esto puede variar.
            # En tu código anterior usabas algo como:
            data_str = resp.output[0].content[0].text  # JSON en texto
            obj = json.loads(data_str)

            title = (obj.get("title") or "").strip()
            if not title:
                return None

            dt_str = obj.get("datetime")
            dt_obj: Optional[datetime] = None
            if dt_str:
                # Soportar posible sufijo "Z"
                dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

            kind = (obj.get("kind") or "generic").strip() or "generic"
            repeats = (obj.get("repeats") or "once").strip() or "once"

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=kind,
                repeats=repeats,
            )

        except Exception as e:
            print(f"[EntityExtractor V2] ERROR CRÍTICO: {e}")
            return None
