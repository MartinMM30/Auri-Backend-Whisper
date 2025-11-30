from openai import OpenAI

class IntentEngine:
    def __init__(self, client: OpenAI = None):
        # Usa el cliente recibido o crea uno propio
        self.client = client or OpenAI()

    def _rule_based(self, t):
        t = t.lower()

        if any(k in t for k in ["recorda", "recuérdame", "pon un recordatorio"]):
            return "reminder.create"
        if "quita" in t and "recordatorio" in t:
            return "reminder.remove"

        if any(k in t for k in ["clima", "temperatura", "tiempo"]):
            return "weather.query"

        if any(k in t for k in ["outfit", "qué me pongo", "ropa"]):
            return "outfit.suggest"

        if any(k in t for k in ["cómo estoy", "cómo me ves"]):
            return "user.state"

        if any(k in t for k in ["personalidad", "tu voz"]):
            return "auri.config"

        if any(k in t for k in ["estoy triste", "estresado"]):
            return "emotion.support"

        if any(k in t for k in ["hola", "buenos días", "buenas tardes"]):
            return "smalltalk.greeting"

        if any(k in t for k in ["chiste", "divertido"]):
            return "fun.joke"

        return None

    def _llm(self, text):
        prompt = f"""
Clasifica este mensaje en un solo intent válido:
- reminder.create
- reminder.remove
- weather.query
- outfit.suggest
- knowledge.query
- smalltalk.greeting
- fun.joke
- user.state
- emotion.support
- auri.config
- conversation.general

Mensaje: "{text}"
"""

        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": "Eres un clasificador experto."},
                {"role": "user", "content": prompt},
            ]
        )

        return resp.output_text.strip()

    def detect(self, text):
        rule = self._rule_based(text)
        if rule:
            return rule
        return self._llm(text)
