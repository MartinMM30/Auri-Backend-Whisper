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
    EntityExtractor V4 – estable, robusto y compatible con ActionsEngine.

    Cambios clave:
    - Agrega .extract() como alias de .extract_reminder()
    - Limpieza de JSON mucho más segura
    - Fallback interno si el modelo produce basura
    - Compatibilidad SP/EN/PT sin errores
    """

    def __init__(self):
        self.client = OpenAI()

    # ----------------------------------------------------------
    # Limpieza fuerte de JSON
    # ----------------------------------------------------------
    def _clean_json_text(self, raw: str) -> str:
        if not raw:
            return "{}"

        raw = raw.strip()

        # Eliminar bloques de código ```json ... ```
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()

        # Asegurar que solo quede el objeto JSON
        # Buscar primer '{' y último '}'
        if "{" in raw and "}" in raw:
            start = raw.find("{")
            end = raw.rfind("}")
            raw = raw[start:end + 1]

        return raw.strip()

    # ----------------------------------------------------------
    # NUEVO: alias para ActionsEngine
    # ----------------------------------------------------------
    def extract(self, text: str, now: Optional[datetime] = None):
        """
        Alias requerido por ActionsEngine.
        No modificar: ActionsEngine llama a extractor.extract().
        """
        return self.extract_reminder(text, now)

    # ----------------------------------------------------------
    # Motor principal
    # ----------------------------------------------------------
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

REGLAS IMPORTANTES:

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

3) Días de la semana:
   "el viernes" → próximo viernes 09:00
   "el lunes a las 3" → próximo lunes 15:00

4) Hora:
   Si el usuario da hora → respétala.
   Si solo da fecha → 09:00.
   Si no hay hora ni fecha → datetime = null.

5) Repeticiones:
   "todos los días" → daily
   "cada semana" → weekly
   "cada mes" → monthly
   Por defecto: once.

6) Categoría:
   Pagos → payment
   Cumpleaños → birthday
   Clases → class
   Eventos → event
   Otros → generic

7) BORRADOS:
   Si el mensaje contiene "borra", "borre", "elimina", "delete",
   NO modifiques el título. El motor de acciones decide si es delete.

8) FORMATO OBLIGATORIO:
   Devuelve SOLO JSON. Sin explicaciones, sin comentarios.

CONTEXTO:
- now_iso: {now_iso}
- now_date: {now_date}
- now_time: {now_time}

MENSAJE:
\"\"\"{text}\"\"\"
"""

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {"role": "system", "content": "Devuelve SOLO JSON válido."},
                    {"role": "user", "content": prompt},
                ],
            )

            raw = resp.choices[0].message.content or ""
            cleaned = self._clean_json_text(raw)

            try:
                obj = json.loads(cleaned)
            except Exception:
                print("[EntityExtractor] JSON inválido devuelto por LLM:")
                print(raw)
                return None

            # Extraer valores
            title = (obj.get("title") or "").strip()
            if not title:
                return None

            # Fecha y hora
            dt_str = obj.get("datetime")
            dt_obj = None
            if dt_str:
                try:
                    dt_obj = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
                except Exception:
                    dt_obj = None

            return ExtractedReminder(
                title=title,
                datetime=dt_obj,
                kind=obj.get("kind", "generic"),
                repeats=obj.get("repeats", "once")
            )

        except Exception as e:
            print("[EntityExtractor] ERROR CRÍTICO:", e)
            return None
