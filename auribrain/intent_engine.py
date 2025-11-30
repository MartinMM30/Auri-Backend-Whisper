# auribrain/intent_engine.py

import json
from typing import Dict, Any

class IntentEngine:
    """
    Intent Engine completo — interpreta el mensaje usando un LLM
    y devuelve JSON estructurado con intent, entities y assistant_response.
    """

    def __init__(self, client):
        self.client = client  # openai client

    # ---------------------------------------------------------
    # MAIN DETECT — usa el LLM para extraer intención y datos
    # ---------------------------------------------------------
    def detect(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:

        system = f"""
Eres el Intent Engine de Auri.

Tu única tarea es devolver un JSON válido que describa:
- intent: nombre único
- entities: objeto con parámetros extraídos
- assistant_response: frase breve y amable que Auri podría decir

Nunca devuelvas nada fuera de JSON.

Contexto del usuario:
{json.dumps(context, indent=2)}

Intents soportados:
- reminder.create
- reminder.remove
- weather.query
- outfit.suggest
- user.state
- emotion.support
- smalltalk.greeting
- fun.joke
- auri.config
- conversation.general
- unknown

Ejemplos de entidades:
- title
- datetime (ISO)
- date
- time
- city
- emotion
- ui_target

Responde solo con JSON.
"""

        user_prompt = f"Usuario dijo: {message}"

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ]
        )

        raw = resp.output_text.strip()

        try:
            return json.loads(raw)
        except:
            return {
                "intent": "unknown",
                "entities": {},
                "assistant_response": "No estoy segura, ¿podrías repetirlo?"
            }
