# auribrain/weather_advice_engine.py

class WeatherAdviceEngine:
    """Modo Weather Advice – consejos de ropa y riesgos según clima."""

    def detect(self, ctx: dict) -> str | None:
        weather = ctx.get("weather", {})
        desc = (weather.get("description") or "").lower()
        temp = weather.get("temp")

        if "lluv" in desc or "tormenta" in desc:
            return "rain"

        try:
            if temp is not None:
                t = float(temp)
                if t < 15:
                    return "cold"
                if t > 30:
                    return "hot"
        except:
            pass

        return None

    def respond(self, mode: str) -> str:
        if mode == "rain":
            return "Parece que va a llover ☔. Llevá chaqueta o paraguas."
        if mode == "cold":
            return "Hoy pinta frío ❄️. Llevá algo abrigado."
        if mode == "hot":
            return "Hace bastante calor 🔥. Hidratate bien y usá ropa ligera."
        return ""
