# auribrain/response_engine.py

class ResponseEngine:
    """
    ResponseEngine V4 — Emotional Post-Processor

    Toma la respuesta del LLM y la adapta emocionalmente usando:
    - emotion_state["overall"]
    - personality_style
    """

    def apply_emotional_style(self, text: str, emotion_state: dict, personality_style: dict) -> str:
        if not text:
            return text

        overall = emotion_state.get("overall", "neutral")
        energy = emotion_state.get("energy", 0.5)
        stress = emotion_state.get("stress", 0.2)
        affection = emotion_state.get("affection", 0.4)

        tone = personality_style["tone"]
        emoji = personality_style["emoji"]

        # ---------------------------
        # 🎭 PLANTILLAS EMOCIONALES
        # ---------------------------

        if overall == "happy":
            text = (
                f"{text}\n"
                "✨ Me alegra mucho escucharte así, de verdad. "
                f"{emoji or '💛'}"
            )

        elif overall == "affectionate":
            text = (
                "Aw… 💖 " + text +
                "\nEstoy contigo, cerquita, cuando me necesites."
            )

        elif overall == "empathetic":
            text = (
                "Mm… entiendo lo que estás sintiendo…\n"
                f"{text}\n"
                "No estás solo, estoy aquí contigo. 💜"
            )

        elif overall == "tired":
            text = (
                "Déjame hablarte suavecito… 💤\n"
                f"{text}\n"
                "Descansa un poquito… estoy aquí contigo."
            )

        elif overall == "stressed":
            text = (
                f"{text}\n"
                "Respira conmigo, vamos paso a paso… 🫂"
            )

        elif overall == "sad":
            text = (
                "Lamento que estés pasando por un momento así… 💜\n"
                f"{text}"
            )

        # ---------------------------
        # PERSONALIDAD (capa final)
        # ---------------------------

        if tone == "suave y calmado":
            text = "⋯ " + text.replace("!", "").replace("?", "…")

        if tone == "dulce y expresiva":
            text = text + " ✨"

        if tone == "amigable":
            text = text + " 😊"

        if tone == "afectiva y suave":
            text = "💖 " + text + " 💖"

        return text
