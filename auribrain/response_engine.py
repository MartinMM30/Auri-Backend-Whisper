class ResponseEngine:

    def build(self, intent, style, context, memory, user_msg, raw_answer):

        txt = user_msg.lower()
        user = context.get("user", {})
        weather = context.get("weather", {})
        events = context.get("events", [])
        bills = context.get("bills", [])

        # ------- Nombre -------
        if "mi nombre" in txt or "cómo me llamo" in txt:
            if user.get("name"):
                return f"Te llamas {user['name']}."
            return "Aún no sé tu nombre."

        # ------- Ciudad -------
        if "dónde vivo" in txt or "mi ciudad" in txt:
            if user.get("city"):
                return f"Vives en {user['city']}."
            return "Todavía no tengo tu ciudad."

        # ------- Cumpleaños -------
        if "cumple" in txt:
            if user.get("birthday"):
                return f"Tu cumpleaños es el {user['birthday']}."
            return "Aún no tengo tu fecha de cumpleaños."

        # ------- Agenda -------
        if "qué tengo hoy" in txt or "agenda" in txt:
            today = [e for e in events if e.get("when")]
            if not today:
                return "Hoy no tienes eventos programados."
            return "Hoy tienes: " + ", ".join(e["title"] for e in today)

        # ------- Pagos -------
        if "pago" in txt or "debo pagar" in txt:
            if not bills:
                return "No tienes pagos registrados."
            nearest = sorted(bills, key=lambda b: b["due"])[0]
            return f"Tu próximo pago es {nearest['title']} para el {nearest['due']}."

        # ------- Clima -------
        if "clima" in txt:
            if not weather.get("temp"):
                return "Aún no tengo el clima. Intenta sincronizarlo."
            city = user.get("city", "tu ciudad")
            return f"En {city} está {weather['temp']}°C y {weather['description']}."

        # ------- FALLBACK -------
        return raw_answer
