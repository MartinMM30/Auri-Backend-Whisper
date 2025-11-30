class ResponseEngine:

    def build(self, intent, style, context, memory, user_msg, raw_answer):

        txt = user_msg.lower()

        # -----------------------------------------
        # 🌦 OVERRIDE DE CLIMA CORREGIDO
        # -----------------------------------------
        if "clima" in txt or "temperatura" in txt or "tiempo" in txt:

            w = context.get("weather")
            u = context.get("user", {})
            city = u.get("city", "tu ciudad")

            if not w:
                return f"No tengo clima sincronizado aún. Actualiza tu ubicación primero."

            temp = w.get("temp")
            desc = w.get("description")

            return f"Ahora mismo en {city} está {temp}°C con {desc}."

        # -----------------------------------------
        # RECORDATORIOS y ACCIONES
        # (creados por ActionsEngine)
        # -----------------------------------------
        action = memory.last_action
        if action:
            memory.last_action = None
            return raw_answer

        return raw_answer
