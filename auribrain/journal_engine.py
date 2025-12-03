# auribrain/journal_engine.py

class JournalEngine:
    """Modo Journal emocional automático (no cambia respuesta, solo guarda memoria)."""

    def detect(self, user_msg: str, emotion_snapshot: dict) -> bool:
        emo = emotion_snapshot.get("overall", "neutral")
        t = (user_msg or "").lower()

        # emociones fuertes → se guarda en diario
        if emo in ["happy", "sad", "stressed", "affectionate", "empathetic"]:
            return True

        # referencias a días → se guarda
        if any(x in t for x in ["hoy", "esta semana", "estos días", "estos dias"]):
            return True

        return False

    def generate_entry(self, user_msg: str, emotion_snapshot: dict) -> str:
        emo = emotion_snapshot.get("overall", "neutral")
        return f"[JOURNAL] mood={emo} | text={user_msg}"
