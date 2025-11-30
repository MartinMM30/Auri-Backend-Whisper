class ResponseEngine:
    def __init__(self):
        pass

    def intent_templates(self):
        return {
            "reminder.create": "Te configuro ese recordatorio.",
            "reminder.remove": "Listo, quito ese recordatorio.",
            "weather.query": "Te cuento el clima.",
            "outfit.suggest": "Déjame ver qué te recomiendo.",
            "user.state": "Estoy pensando en cómo ayudarte.",
            "emotion.support": "Estoy aquí para ti.",
            "auri.config": "Claro, ajustemos tu configuración.",
            "knowledge.query": "Te explico.",
            "smalltalk.greeting": "Hola.",
            "fun.joke": "Aquí va uno.",
            "conversation.general": "",
            "unknown": "",
        }

    def build(self, intent, style, context, memory, user_msg, raw_answer):
        base = self.intent_templates()
        prefix = base.get(intent, "")

        # Respuesta PRINCIPAL = lo que diga el modelo,
        # sin contexto extra ni “recuerdo que antes dijiste…”
        text = raw_answer.strip()

        # Prefijo corto según intención (si existe)
        if prefix:
            final = f"{prefix} {text}".strip()
        else:
            final = text

        # Recortar si se descontrola
        if len(final) > 260:
            final = final[:250].rsplit(" ", 1)[0] + "…"

        return final
