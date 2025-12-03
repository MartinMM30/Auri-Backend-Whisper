# auribrain/emotion_engine.py

from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class EmotionEngine:
    """
    EmotionEngine V8 (mejorado)

    Fusiona:
    - Emoción por texto
    - Emoción por voz (cuando esté disponible)
    - Contexto diario (pagos, clima, agenda, hora del día)
    - Memoria emocional interna temporal

    Expone:
    - update(user_text, context, voice_emotion=None) -> dict
    - get_state()
    - get_slime_state()
    """

    def __init__(self) -> None:
        now = datetime.utcnow()
        self.state: Dict[str, Any] = {
            "auri_mood": "neutral",
            "user_emotion_text": "neutral",
            "user_emotion_voice": "neutral",
            "overall": "neutral",

            "energy": 0.6,
            "stress": 0.2,
            "affection": 0.4,
            "focus": 0.5,

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

    # ------------------------------------------------------
    # API PRINCIPAL
    # ------------------------------------------------------
    def update(
        self,
        user_text: str,
        context: Dict[str, Any],
        voice_emotion: Optional[str] = None,
    ) -> Dict[str, Any]:

        now = datetime.utcnow()
        self._apply_time_decay(now)

        # 1) Texto → emoción
        text_emotion = self._detect_text_emotion(user_text or "")
        self.state["user_emotion_text"] = text_emotion

        # 2) Voz → emoción (si está)
        voice_em = self._normalize_voice_emotion(voice_emotion)
        self.state["user_emotion_voice"] = voice_em

        # 3) Contexto → flags
        self._update_context_flags(context)

        # 4) Aplicar impactos
        self._apply_text_impact(text_emotion)
        self._apply_voice_impact(voice_em)
        self._apply_context_impact(context)

        # 5) Resolver estado emocional final
        overall = self._resolve_overall_state()
        self.state["overall"] = overall
        self.state["auri_mood"] = overall

        # finalizar actualización
        self.state["last_update"] = now
        self.state["last_user_text"] = user_text

        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        return dict(self.state)

    def get_slime_state(self) -> Dict[str, Any]:
        """Mapa limpio para animación en Rive"""
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

    # ------------------------------------------------------
    # TIME DECAY – regula energía/estrés cuando pasa el tiempo
    # ------------------------------------------------------
    def _apply_time_decay(self, now: datetime) -> None:
        last = self.state.get("last_update") or now
        elapsed = (now - last).total_seconds()

        if elapsed < 60:
            return

        steps = elapsed / 300.0  # cada 5 minutos

        self.state["stress"] = max(0.0, self.state["stress"] - 0.05 * steps)
        self.state["affection"] = max(0.0, self.state["affection"] - 0.02 * steps)
        self.state["energy"] = min(1.0, self.state["energy"] + 0.03 * steps)

    # ------------------------------------------------------
    # DETECCIÓN EMOCIONAL POR TEXTO
    # ------------------------------------------------------
    def _detect_text_emotion(self, text: str) -> str:
        t = (text or "").lower().strip()
        if not t:
            return "neutral"

        # depresivo / tristeza fuerte
        sad_words = [
            "triste", "deprimido", "mal", "muy mal", "vacío", "solo",
            "desanimado", "llorando", "agotado", "quebrado", "drained",
        ]
        if any(w in t for w in sad_words):
            if "feliz" in t or "contento" in t:
                return "mixed_tired_happy"
            return "sad"

        # ansiedad / preocupación
        anxious = [
            "ansioso", "ansiosa", "ansiedad", "preocupado", "nervioso",
            "miedo", "temor", "inquieto", "overthinking",
        ]
        if any(w in t for w in anxious):
            return "worried"

        # enojo
        angry = [
            "enojado", "molesto", "furioso", "irritado", "harto",
            "raiva", "bravo", "angry", "mad",
        ]
        if any(w in t for w in angry):
            return "angry"

        # afecto
        affection = [
            "te quiero", "te amo", "me gustas", "eres importante",
            "me haces feliz", "te extraño", "love you", "amo você",
        ]
        if any(w in t for w in affection):
            return "affectionate"

        # felicidad
        happy = [
            "feliz", "contento", "genial", "perfecto", "me fue bien",
            "muy bien", "emocionado", "animado", "increíble", "awesome",
        ]
        if any(w in t for w in happy):
            return "happy"

        # aburrimiento
        bored = [
            "aburrido", "tedioso", "no sé qué hacer", "bored",
        ]
        if any(w in t for w in bored):
            return "bored"

        # cansancio
        tired = [
            "cansado", "cansada", "exhausto", "exausta",
            "muy cansado", "muito cansado",
        ]
        if any(w in t for w in tired):
            return "tired"

        return "neutral"

    # ------------------------------------------------------
    # EMOCIÓN DE VOZ (cuando llegue modelo acústico)
    # ------------------------------------------------------
    def _normalize_voice_emotion(self, voice_emotion: Optional[str]) -> str:
        if not voice_emotion:
            return "neutral"

        mapping = {
            "joy": "happy",
            "happiness": "happy",
            "sadness": "sad",
            "anger": "angry",
            "fear": "worried",
            "anxiety": "worried",
            "tired": "tired",
            "calm": "calm",
        }
        v = voice_emotion.lower().strip()
        return mapping.get(v, v)

    # ------------------------------------------------------
    # FLAGS DESDE CONTEXTO (pagos, clima, agenda)
    # ------------------------------------------------------
    def _update_context_flags(self, ctx: Dict[str, Any]) -> None:
        flags = self.state["context_flags"]

        weather = (ctx.get("weather") or {})
        desc = (weather.get("description") or "").lower()
        flags["bad_weather"] = any(k in desc for k in ["lluvia", "tormenta", "nublado", "storm", "rain"])

        # pagos y eventos próximos
        events = ctx.get("events") or []
        soon = 0
        now_iso = ctx.get("current_time_iso")
        try:
            now = datetime.fromisoformat(now_iso) if now_iso else datetime.utcnow()
        except:
            now = datetime.utcnow()

        for ev in events:
            when = ev.get("when")
            if not when:
                continue
            try:
                dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
                if 0 <= (dt - now).total_seconds() / 86400 <= 3:
                    soon += 1
            except:
                pass

        flags["many_events_soon"] = soon >= 4
        flags["many_payments_soon"] = len(ctx.get("payments") or []) >= 4

        # hora del día
        try:
            hour = int((ctx.get("current_time_pretty", "12:00").split(":")[0]))
        except:
            hour = 12

        flags["morning_time"] = 5 <= hour < 12
        flags["night_time"] = hour >= 21 or hour < 5

    # ------------------------------------------------------
    # IMPACTOS AL ESTADO INTERNO
    # ------------------------------------------------------
    def _apply_text_impact(self, emo: str) -> None:
        if emo in ["sad", "worried", "angry", "tired", "mixed_tired_happy"]:
            self.state["affection"] = min(1.0, self.state["affection"] + 0.15)

        if emo == "sad":
            self.state["stress"] = min(1.0, self.state["stress"] + 0.15)
            self.state["energy"] -= 0.1

        elif emo == "worried":
            self.state["stress"] += 0.2
            self.state["focus"] -= 0.05

        elif emo == "angry":
            self.state["stress"] += 0.25
            self.state["focus"] += 0.05

        elif emo == "affectionate":
            self.state["affection"] += 0.25
            self.state["stress"] -= 0.05

        elif emo == "happy":
            self.state["energy"] += 0.15
            self.state["stress"] -= 0.1

        elif emo == "bored":
            self.state["energy"] -= 0.05
            self.state["focus"] -= 0.05

        elif emo == "tired":
            self.state["energy"] -= 0.15
            self.state["stress"] += 0.05

        elif emo == "mixed_tired_happy":
            self.state["energy"] -= 0.05
            self.state["stress"] -= 0.05
            self.state["affection"] += 0.1

    def _apply_voice_impact(self, emo: str) -> None:
        if emo == "happy":
            self.state["energy"] += 0.1
        elif emo in ["sad", "tired"]:
            self.state["energy"] -= 0.1
            self.state["stress"] += 0.05
        elif emo == "angry":
            self.state["stress"] += 0.1

    def _apply_context_impact(self, ctx: Dict[str, Any]) -> None:
        flags = self.state["context_flags"]

        if flags["bad_weather"]:
            self.state["energy"] -= 0.05

        if flags["many_payments_soon"] or flags["many_events_soon"]:
            self.state["stress"] += 0.15

        if flags["night_time"]:
            self.state["energy"] -= 0.1
        elif flags["morning_time"]:
            self.state["energy"] += 0.05

        # clases/exámenes → más foco
        if (ctx.get("exams") or []) or (ctx.get("classes") or []):
            self.state["focus"] += 0.05

        # clamping final
        self.state["energy"] = max(0.0, min(1.0, self.state["energy"]))
        self.state["stress"] = max(0.0, min(1.0, self.state["stress"]))
        self.state["affection"] = max(0.0, min(1.0, self.state["affection"]))
        self.state["focus"] = max(0.0, min(1.0, self.state["focus"]))

    # ------------------------------------------------------
    # RESOLUCIÓN EMOCIONAL
    # ------------------------------------------------------
    def _resolve_overall_state(self) -> str:
        emo = self.state["user_emotion_text"]
        e = self.state["energy"]
        s = self.state["stress"]
        a = self.state["affection"]

        # modo cariño
        if a > 0.7 and emo in ["happy", "affectionate"]:
            return "affectionate"

        # empatía (usuario triste)
        if emo in ["sad", "worried"]:
            return "empathetic"

        # estrés alto
        if s > 0.7:
            return "stressed"

        # cansancio
        if e < 0.3:
            return "tired"

        # feliz
        if emo in ["happy", "mixed_tired_happy"] or e > 0.75:
            return "happy"

        # gris / melancólico leve
        if emo in ["bored"]:
            return "sad"

        return "neutral"
