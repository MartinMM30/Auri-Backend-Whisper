import random

class PersonalityEngine:

    def __init__(self):
        self.current = "auri_classic"

        self.styles = {
            "auri_classic": {
                "tone": "cálido, cercano y ligeramente juguetón",
                "traits": ["empático", "positivo", "humano"]
            },
            "auri_jarvis": {
                "tone": "sereno y profesional",
                "traits": ["claro", "directo"]
            },
            "auri_friendly": {
                "tone": "muy alegre y amable",
                "traits": ["luminoso", "entusiasta"]
            },
            "auri_stoic": {
                "tone": "tranquilo y minimalista",
                "traits": ["reflexivo", "neutral"]
            },
            "auri_romantic": {
                "tone": "dulce y cariñoso",
                "traits": ["tierno", "gentil"]
            },
        }

    def set_personality(self, key):
        if key in self.styles:
            self.current = key
        else:
            print(f"⚠ Personalidad '{key}' no existe, usando clásica")

    # ---------------------------------------------------------
    def emotional_adjustment(self, emo):
        return {
            "tired": "más suave y calmado",
            "sad": "reconfortante y muy cálido",
            "angry": "neutral y equilibrado",
            "happy": "más expresivo y positivo"
        }.get(emo)

    # ---------------------------------------------------------
    def contextual_adjustment(self, ctx):
        parts = []

        # WEATHER
        w = ctx.get("weather", {})
        desc = ""

        if isinstance(w, dict):
            desc = (w.get("description") or "").lower()
        elif isinstance(w, str):
            desc = w.lower()

        if "lluv" in desc:
            parts.append("algo reflexivo por la lluvia")
        elif "nub" in desc or "cloud" in desc:
            parts.append("tranquilo por el clima nublado")
        elif "sole" in desc:
            parts.append("animado por el sol")

        # WORKLOAD
        events = ctx.get("events", [])
        if len(events) >= 4:
            parts.append("más organizado para ayudarte hoy")

        # BILLS
        bills = ctx.get("bills", [])
        if bills:
            parts.append("considerando que hoy tienes pendientes importantes")

        return ", ".join(parts) if parts else None

    # ---------------------------------------------------------
    def build_final_style(self, context, emotion):
        base = self.styles.get(self.current, self.styles["auri_classic"])

        tone = base["tone"]
        traits = base["traits"]

        emo_adj = self.emotional_adjustment(emotion)
        if emo_adj:
            tone += f", {emo_adj}"

        ctx_adj = self.contextual_adjustment(context)
        if ctx_adj:
            tone += f", {ctx_adj}"

        tone += ", " + random.choice([
            "con un toque humano",
            "de forma natural",
            "con suavidad",
            "con mucha cercanía",
            "de forma auténtica"
        ])

        return {
            "tone": tone,
            "traits": traits,
            "active_personality": self.current
        }
