import random

class PersonalityEngine:
    def __init__(self):
        self.current = "auri_classic"

        self.styles = {
            "auri_classic": {
                "tone": "cálido, comprensivo y algo juguetón",
                "traits": ["empático", "motivador", "positivo"]
            },
            "auri_jarvis": {
                "tone": "sereno, profesional y preciso",
                "traits": ["analítico", "estratégico"]
            },
            "auri_friendly": {
                "tone": "muy alegre, amable y optimista",
                "traits": ["sociable", "luminoso"]
            },
            "auri_stoic": {
                "tone": "tranquilo y minimalista",
                "traits": ["neutral", "reflexivo"]
            },
            "auri_romantic": {
                "tone": "dulce, gentil y cariñoso",
                "traits": ["afectuoso", "tierno"]
            },
        }

    def set_personality(self, key):
        if key in self.styles:
            self.current = key
        else:
            print(f"⚠️ Personalidad '{key}' no existe, usando clásico")

    def emotional_adjustment(self, emo):
        return {
            "tired": "más suave y calmado",
            "sad": "muy cálido y reconfortante",
            "angry": "neutral, diplomático y claro",
            "happy": "más expresivo y positivo"
        }.get(emo)

    def contextual_adjustment(self, ctx):
        parts = []

        weather = ctx.get("weather", "").lower()
        tod = ctx.get("time_of_day", "")
        workload = ctx.get("workload", "")
        energy = ctx.get("energy", "")

        if "rain" in weather:
            parts.append("un poco reflexivo por la lluvia")
        elif "sun" in weather:
            parts.append("más animado por el clima soleado")

        if tod == "night":
            parts.append("tranquilo por la hora")
        elif tod == "morning":
            parts.append("energético para arrancar el día")

        if workload == "overloaded":
            parts.append("directo y organizado para ayudarte")
        elif workload == "busy":
            parts.append("eficiente y claro")

        if energy == "low":
            parts.append("cuidadoso para no agobiarte")

        return ", ".join(parts) if parts else None

    def build_final_style(self, context, emotion):
        base = self.styles.get(self.current)

        tone = base["tone"]
        traits = base["traits"]

        emo_adj = self.emotional_adjustment(emotion)
        if emo_adj:
            tone += f", {emo_adj}"

        ctx_adj = self.contextual_adjustment(context)
        if ctx_adj:
            tone += f", {ctx_adj}"

        tone += ", " + random.choice([
            "con un toque natural",
            "de forma muy humana",
            "con suavidad",
            "manteniendo cercanía",
            "de manera auténtica"
        ])

        return {
            "tone": tone,
            "traits": traits,
            "active_personality": self.current
        }
