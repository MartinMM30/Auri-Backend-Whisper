from datetime import datetime
from typing import Dict, Any, Optional


class EmotionEngine:
    """
    EmotionEngine V8 — Integración completa de emoción por voz.
    -----------------------------------------------------------
    Combina 3 señales:

    - user_emotion_text  → emoción explícita
    - user_emotion_voice → emoción acústica (más honesta)
    - contexto           → clima, pagos, horario, etc.

    Produce:
    - overall            → estado final para respuestas y Rive
    - auri_mood          → estado interno persistente
    """

    def __init__(self):
        now = datetime.utcnow()
        self.state: Dict[str, Any] = {
            "auri_mood": "neutral",

            "user_emotion_text": "neutral",
            "user_emotion_voice": "neutral",
            "combined_emotion": "neutral",

            "energy": 0.6,
            "stress": 0.2,
            "affection": 0.4,
            "focus": 0.5,

            "overall": "neutral",
            "last_update": now,
            "last_user_text": "",
            "context_flags": {
                "bad_weather": False,
                "many_payments_soon": False,
                "many_events_soon": False,
                "night_time": False,
                "morning_time": False,
            },
        }

    # ----------------------------------------------------
    # ENTRY POINT
    # ----------------------------------------------------
    def update(self, user_text: str, context: dict, voice_emotion: Optional[str]):
        now = datetime.utcnow()
        self._apply_time_decay(now)

        # 1) detectar texto
        text_emo = self._detect_text_emotion(user_text or "")
        self.state["user_emotion_text"] = text_emo

        # 2) normalizar voz
        voice_emo = self._normalize_voice_emotion(voice_emotion)
        self.state["user_emotion_voice"] = voice_emo

        # 3) flags desde contexto
        self._update_context_flags(context)

        # 4) impacto texto
        self._apply_text_impact(text_emo)

        # 5) impacto voz
        self._apply_voice_impact(voice_emo)

        # 6) fusionar emociones
        combined = self._combine_emotions(text_emo, voice_emo)
        self.state["combined_emotion"] = combined

        # 7) impacto del combinado
        self._apply_combined_impact(combined)

        # 8) aplicar contexto
        self._apply_context_impact(context)

        # 9) resolver estado global
        overall = self._resolve_overall_state()
        self.state["overall"] = overall
        self.state["auri_mood"] = overall

        self.state["last_update"] = now
        self.state["last_user_text"] = user_text

        return self.get_state()

    # ----------------------------------------------------
    def get_state(self):
        return dict(self.state)

    def get_slime_state(self):
        o = self.state["overall"]
        return {
            "overall": o,
            "mood_happy": o == "happy",
            "mood_sad": o == "sad",
            "mood_tired": o == "tired",
            "mood_stressed": o == "stressed",
            "mood_empathetic": o == "empathetic",
            "mood_affectionate": o == "affectionate",
            "mood_neutral": o == "neutral",
            "energy_level": self.state["energy"],
            "stress_level": self.state["stress"],
            "affection_level": self.state["affection"],
        }

    # ======================================================
    # TIME DECAY
    # ======================================================
    def _apply_time_decay(self, now):
        last = self.state["last_update"]
        elapsed = (now - last).total_seconds()
        if elapsed < 60:
            return

        steps = elapsed / 300.0
        self.state["stress"] = max(0, self.state["stress"] - 0.05 * steps)
        self.state["energy"] = min(1, self.state["energy"] + 0.03 * steps)
        self.state["affection"] = max(0, self.state["affection"] - 0.02 * steps)

    # ======================================================
    # TEXT EMOTION DETECTION
    # ======================================================
    def _detect_text_emotion(self, t: str) -> str:
        t = t.lower()

        sad_words = ["triste", "mal", "vacío", "solo", "sola", "cansado", "cansada",
                     "agotado", "agotada", "llorando", "deprimido", "deprimida"]
        anxious_words = ["ansioso", "ansiosa", "preocupado", "preocupada", "miedo"]
        angry_words = ["enojado", "enojada", "molesto", "furioso", "rabia", "harto"]
        affectionate_words = ["te quiero", "te amo", "me gustas", "eres importante"]
        happy_words = ["feliz", "contento", "contenta", "genial", "muy bien", "perfecto"]

        if any(w in t for w in sad_words): return "sad"
        if any(w in t for w in anxious_words): return "worried"
        if any(w in t for w in angry_words): return "angry"
        if any(w in t for w in affectionate_words): return "affectionate"
        if any(w in t for w in happy_words): return "happy"
        if "cansad" in t: return "tired"
        return "neutral"

    # ======================================================
    # VOICE EMOTION NORMALIZATION
    # ======================================================
    def _normalize_voice_emotion(self, v):
        if not v:
            return "neutral"
        v = v.lower().strip()
        mapping = {
            "joy": "happy",
            "happiness": "happy",
            "sadness": "sad",
            "fear": "worried",
            "anxiety": "worried",
            "tired": "tired",
            "anger": "angry",
            "angry": "angry",
            "calm": "neutral",
        }
        return mapping.get(v, v)

    # ======================================================
    # IMPACTO POR TEXTO
    # ======================================================
    def _apply_text_impact(self, emo):
        if emo == "sad":
            self.state["stress"] += 0.15
            self.state["energy"] -= 0.1
            self.state["affection"] += 0.1

        elif emo == "worried":
            self.state["stress"] += 0.2
            self.state["focus"] -= 0.05

        elif emo == "angry":
            self.state["stress"] += 0.25
            self.state["energy"] -= 0.05

        elif emo == "affectionate":
            self.state["affection"] += 0.25
            self.state["stress"] -= 0.05

        elif emo == "happy":
            self.state["energy"] += 0.15
            self.state["stress"] -= 0.1

        elif emo == "tired":
            self.state["energy"] -= 0.15
            self.state["stress"] += 0.05

    # ======================================================
    # IMPACTO POR VOZ (NUEVO / FUERTE)
    # ======================================================
    def _apply_voice_impact(self, emo):
        if emo == "happy":
            self.state["energy"] += 0.12
            self.state["affection"] += 0.1

        elif emo == "sad":
            self.state["energy"] -= 0.12
            self.state["stress"] += 0.1

        elif emo == "tired":
            self.state["energy"] -= 0.18

        elif emo == "angry":
            self.state["stress"] += 0.18
            self.state["energy"] -= 0.05

    # ======================================================
    # FUSIÓN TEXTO + VOZ (CLAVE)
    # ======================================================
    def _combine_emotions(self, text, voice):
        # coincidencia → amplificar
        if text == voice:
            return text

        # tristeza en voz + neutral en texto → tristeza escondida
        if voice == "sad" and text == "neutral":
            return "hidden_sad"

        # cansancio en voz + texto normal → agotamiento real
        if voice == "tired" and text == "neutral":
            return "hidden_tired"

        # enojo en voz + texto calmado → enojo reprimido
        if voice == "angry" and text in ["neutral", "worried"]:
            return "suppressed_anger"

        # texto feliz + voz cansada = conflicto emocional
        if text == "happy" and voice == "tired":
            return "mixed_conflict"

        # si ninguna regla especial → priorizar texto
        return text

    # ======================================================
    # IMPACTO DE EMOCIONES COMBINADAS
    # ======================================================
    def _apply_combined_impact(self, emo):
        if emo == "hidden_sad":
            self.state["affection"] += 0.15
            self.state["stress"] += 0.1

        elif emo == "hidden_tired":
            self.state["energy"] -= 0.15

        elif emo == "suppressed_anger":
            self.state["stress"] += 0.25

        elif emo == "mixed_conflict":
            self.state["energy"] -= 0.05
            self.state["affection"] += 0.05

    # ======================================================
    # CONTEXTO
    # ======================================================
    def _update_context_flags(self, ctx):
        flags = self.state["context_flags"]
        weather = ctx.get("weather", {})
        desc = (weather.get("description") or "").lower()

        flags["bad_weather"] = any(k in desc for k in ["lluvia", "tormenta", "storm"])

        events = ctx.get("events", [])
        flags["many_events_soon"] = len(events) >= 5

        payments = ctx.get("payments", [])
        flags["many_payments_soon"] = len(payments) >= 4

        hour = int((ctx.get("current_time_pretty", "12:00").split(":")[0]))
        flags["night_time"] = hour >= 22 or hour < 6
        flags["morning_time"] = 6 <= hour < 12

    # ======================================================
    # IMPACTO DEL CONTEXTO
    # ======================================================
    def _apply_context_impact(self, ctx):
        flags = self.state["context_flags"]

        if flags["bad_weather"]:
            self.state["energy"] -= 0.05

        if flags["many_events_soon"] or flags["many_payments_soon"]:
            self.state["stress"] += 0.15

        if flags["night_time"]:
            self.state["energy"] -= 0.1
        elif flags["morning_time"]:
            self.state["energy"] += 0.05

        exams = ctx.get("exams") or []
        if exams:
            self.state["focus"] += 0.05

        # clamp
        for k in ["energy", "stress", "affection", "focus"]:
            self.state[k] = max(0.0, min(1.0, self.state[k]))

    # ======================================================
    # ESTADO GLOBAL FINAL
    # ======================================================
    def _resolve_overall_state(self):
        emo = self.state["combined_emotion"]
        energy = self.state["energy"]
        stress = self.state["stress"]
        affection = self.state["affection"]

        # priorizar combinaciones especiales
        if emo in ["hidden_sad", "hidden_tired", "suppressed_anger"]:
            return "empathetic"

        if emo == "sad":
            return "empathetic"

        if emo == "affectionate" or affection > 0.75:
            return "affectionate"

        if emo == "angry" or stress > 0.75:
            return "stressed"

        if emo == "tired" or energy < 0.3:
            return "tired"

        if emo == "happy" or energy > 0.75:
            return "happy"

        return "neutral"
