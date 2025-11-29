class ResponseEngine:
    def __init__(self):
        pass

    # -------------------------------------------------------------------
    # Plantillas base por intención
    # -------------------------------------------------------------------
    def intent_templates(self):
        return {
            "reminder.create": "Ya lo gestiono. Te configuro ese recordatorio.",
            "reminder.remove": "Lo elimino sin problema.",
            "weather.query": "Te cuento cómo está el clima.",
            "outfit.suggest": "Déjame ver qué te recomiendo.",
            "user.state": "Estoy evaluando cómo te encuentras.",
            "emotion.support": "Estoy aquí para ti.",
            "auri.config": "Claro, cambiemos tu configuración.",
            "knowledge.query": "Déjame explicártelo.",
            "smalltalk.greeting": "Claro, hablemos.",
            "fun.joke": "Aquí va uno.",
            "conversation.general": "Perfecto, déjame analizarlo.",
            "unknown": "Lo estoy analizando… dame un segundo."
        }

    # -------------------------------------------------------------------
    # Respuesta final combinando contexto + memoria + estilo + LLM
    # -------------------------------------------------------------------
    def build(self, intent, style, context, memory, user_msg, raw_answer):
        tone = style.get("tone", "")
        traits = style.get("traits", [])

        # ---------- 1. Base por intención ----------
        base = self.intent_templates()
        intent_base = base.get(intent, base["unknown"])

        # ---------- 2. Texto de contexto ----------
        ctx_parts = []

        weather = context.get("weather", "").lower()
        tod = context.get("time_of_day", "")
        energy = context.get("energy", "")
        workload = context.get("workload", "")

        # Clima
        if "rain" in weather:
            ctx_parts.append("Parece que afuera está lluvioso.")
        elif "sun" in weather:
            ctx_parts.append("El clima está soleado y agradable.")

        # Hora del día
        if tod == "night":
            ctx_parts.append("Ya es de noche, trataré de ser más breve.")
        elif tod == "morning":
            ctx_parts.append("Es una buena mañana para organizar tu día.")

        # Energía del usuario
        if energy == "low":
            ctx_parts.append("Noto que tu energía está un poco baja.")
        elif energy == "high":
            ctx_parts.append("Siento que tienes buena energía ahora mismo.")

        # Carga del usuario
        if workload == "busy":
            ctx_parts.append("Tienes bastante en tu agenda.")
        elif workload == "overloaded":
            ctx_parts.append("Tu carga está pesada, puedo ayudarte a organizarla.")

        context_sentence = " ".join(ctx_parts)

        # ---------- 3. Última interacción (memoria corta) ----------
        recent = memory.get_recent()
        mem_line = ""
        if recent:
            mem_line = f"Recuerdo que antes mencionaste algo como: “{recent[-1]}”. "

        # ---------- 4. Ensamble final ----------
        final = f"{intent_base}. "

        if context_sentence:
            final += context_sentence + " "

        if mem_line:
            final += mem_line

        final += f"({tone}). Te cuento lo que he pensado: {raw_answer.strip()}"

        # Suavizar
        final = self._humanize(final)
        return final.strip()

    # -------------------------------------------------------------------
    # Suavizador
    # -------------------------------------------------------------------
    def _humanize(self, text):
        replacements = {
            "Estoy procesando": "Déjame pensarlo un momento",
            "Aquí tienes mi respuesta": "Te cuento lo que he pensado",
            "Te explico": "Mira, lo veo así",
        }

        for k, v in replacements.items():
            text = text.replace(k, v)

        while "  " in text:
            text = text.replace("  ", " ")

        return text
