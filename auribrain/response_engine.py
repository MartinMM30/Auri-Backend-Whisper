# auribrain/response_engine.py

from typing import Any, Dict


class ResponseEngine:
    """
    Se encarga de construir la respuesta final de texto
    usando:
      - intent
      - contexto (clima, usuario, eventos)
      - estilo de personalidad
      - memoria
      - respuesta cruda del LLM (raw_answer)
    """

    def build(
        self,
        intent: str,
        style: Dict[str, Any],
        context: Dict[str, Any],
        memory,
        user_msg: str,
        raw_answer: str,
    ) -> str:
        # =====================================================
        # 1) CLIMA — override duro con contexto
        # =====================================================
        if intent == "weather.query":
            weather_str = context.get("weather") or "unknown"
            user = context.get("user") or {}
            city = None

            if isinstance(user, dict):
                city = user.get("city")

            # Si no hay clima válido en contexto
            if not weather_str or weather_str == "unknown":
                return "Todavía no tengo el clima actualizado, pero pronto podré ayudarte con eso."

            # Si tenemos ciudad, lo hacemos más bonito
            if city:
                return f"Ahora mismo en {city} está {weather_str}."
            else:
                return f"Ahora mismo el clima está {weather_str}."

        # =====================================================
        # 2) Otros intents: usamos la respuesta cruda del LLM
        #    (ya viene limitada a 1–2 frases por el system prompt)
        # =====================================================
        text = (raw_answer or "").strip()
        if not text:
            text = "Lo siento, no estoy seguro de qué responder."

        return text
