# auribrain/emotion_engine.py

from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class EmotionEngine:
    """
    EmotionEngine V7

    Fusiona tres fuentes:
    - Texto del usuario (contenido emocional explícito / implícito)
    - Contexto diario (clima, pagos, exámenes, agenda)
    - Voz (más adelante: etiqueta como 'happy', 'sad', etc.)

    Expone:
    - update(user_text, context, voice_emotion=None) -> dict (snapshot de estado)
    - get_state() -> dict
    - get_slime_state() -> mapping listo para Rive
    """

    def __init__(self) -> None:
        now = datetime.utcnow()
        self.state: Dict[str, Any] = {
            "auri_mood": "neutral",          # cómo se siente Auri por dentro
            "user_emotion_text": "neutral",  # emoción detectada por texto
            "user_emotion_voice": "neutral", # emoción detectada por voz (más adelante)
            "overall": "neutral",            # estado combinado final

            "energy": 0.6,       # 0–1
            "stress": 0.2,       # 0–1
            "affection": 0.4,    # 0–1
            "focus": 0.5,        # 0–1

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
    # API PÚBLICA
    # ------------------------------------------------------
    def update(
        self,
        user_text: str,
        context: Dict[str, Any],
        voice_emotion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal.
        - user_text: texto crudo del usuario
        - context: diccionario del ContextEngine.get_daily_context()
        - voice_emotion: etiqueta simple ("happy", "sad", "angry", etc.) que
                         luego pondremos desde el análisis de audio.
        """

        now = datetime.utcnow()
        self._apply_time_decay(now)

        # 1) Emoción desde texto
        text_emotion = self._detect_text_emotion(user_text or "")
        self.state["user_emotion_text"] = text_emotion

        # 2) Emoción desde voz (opcional, aún podemos pasar None)
        voice_em = self._normalize_voice_emotion(voice_emotion)
        self.state["user_emotion_voice"] = voice_em

        # 3) Flags desde contexto (clima, pagos, exámenes, horario)
        self._update_context_flags(context)

        # 4) Aplicar impactos al estado interno
        self._apply_text_impact(text_emotion)
        self._apply_voice_impact(voice_em)
        self._apply_context_impact(context)

        # 5) Resolver estado global
        overall = self._resolve_overall_state()
        self.state["overall"] = overall
        self.state["auri_mood"] = overall

        self.state["last_update"] = now
        self.state["last_user_text"] = user_text

        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Devuelve un snapshot del estado emocional actual."""
        return dict(self.state)

    def get_slime_state(self) -> Dict[str, Any]:
        """
        Mapeo listo para el Slime (Rive) y el TTS:
        - mood_*: flags de estado
        - energy_level, stress_level, affection_level
        """
        overall = self.state["overall"]
        energy = self.state["energy"]
        stress = self.state["stress"]
        affection = self.state["affection"]

        return {
            "overall": overall,
            "mood_happy": overall == "happy",
            "mood_sad": overall == "sad",
            "mood_tired": overall == "tired",
            "mood_stressed": overall == "stressed",
            "mood_empathetic": overall == "empathetic",
            "mood_affectionate": overall == "affectionate",
            "mood_neutral": overall == "neutral",

            "energy_level": energy,
            "stress_level": stress,
            "affection_level": affection,
        }

    # ------------------------------------------------------
    # DECAY TEMPORAL
    # ------------------------------------------------------
    def _apply_time_decay(self, now: datetime) -> None:
        """
        Si ha pasado mucho tiempo desde la última actualización,
        baja un poco estrés y emoción acumulada para que Auri
        no se quede atrapada en un estado.
        """
        last = self.state.get("last_update") or now
        elapsed = (now - last).total_seconds()

        if elapsed < 60:
            return

        # cada 5 minutos, reducimos un poco
        steps = elapsed / 300.0

        self.state["stress"] = max(0.0, self.state["stress"] - 0.05 * steps)
        self.state["affection"] = max(0.0, min(1.0, self.state["affection"] - 0.02 * steps))

        # energía sube un poco si ha pasado tiempo (como descansar)
        self.state["energy"] = max(0.0, min(1.0, self.state["energy"] + 0.03 * steps))

    # ------------------------------------------------------
    # DETECCIÓN EMOCIONAL DESDE TEXTO
    # ------------------------------------------------------
    def _detect_text_emotion(self, text: str) -> str:
        """
        Heurísticas multi-idioma (es, pt, en básico) para detectar la emoción principal.
        """
        t = (text or "").lower()

        if not t.strip():
            return "neutral"

        # ⚠️ Emociones negativas fuertes primero
        sad_words = [
            "triste", "deprimido", "deprimida", "mal", "vacío", "vacía",
            "solo", "sola", "solitario", "solitaria", "desanimado", "desanimada",
            "cansado", "cansada", "agotado", "agotada", "quebrado",
            "derrotado", "llorando", "llorar",
            "cansado demais", "cansada demais",
            "tired", "exhausted", "drained",
        ]
        if any(w in t for w in sad_words):
            # si además aparecen cosas tipo "cansado" + "feliz", puede ser mixed
            if "feliz" in t or "contento" in t or "contenta" in t or "happy" in t:
                return "mixed_tired_happy"
            return "sad"

        anxious_words = [
            "ansioso", "ansiosa", "ansiedad", "preocupado", "preocupada",
            "nervioso", "nerviosa", "miedo", "temor", "inquieto", "inquieta",
            "overthinking",
        ]
        if any(w in t for w in anxious_words):
            return "worried"

        angry_words = [
            "enojado", "enojada", "molesto", "molesta", "furioso", "furiosa",
            "harto", "harta", "irritado", "irritada", "raiva", "bravo", "brava",
            "angry", "mad",
        ]
        if any(w in t for w in angry_words):
            return "angry"

        affection_words = [
            "te quiero", "te amo", "me gustas", "eres importante",
            "me haces feliz", "te extraño", "sos importante",
            "love you", "i love you", "amo você",
        ]
        if any(w in t for w in affection_words):
            return "affectionate"

        happy_words = [
            "feliz", "contento", "contenta", "genial", "perfecto", "perfecta",
            "me fue bien", "todo bien", "muy bien", "me siento bien",
            "emocionado", "emocionada", "animado", "animada",
            "increíble", "espectacular", "ótimo", "maravilhoso",
            "awesome", "great", "fantastic",
        ]
        if any(w in t for w in happy_words):
            return "happy"

        bored_words = [
            "aburrido", "aburrida", "no sé qué hacer", "nada que hacer",
            "tedioso", "cansado de todo", "bored",
        ]
        if any(w in t for w in bored_words):
            return "bored"

        # mención explícita de cansancio sin otras cosas muy negativas
        tired_words = [
            "cansado", "cansada", "exhausto", "exausta",
            "muito cansado", "muito cansada",
        ]
        if any(w in t for w in tired_words):
            return "tired"

        return "neutral"

    # ------------------------------------------------------
    # VOZ (por ahora etiqueta, luego PCM→modelo)
    # ------------------------------------------------------
    def _normalize_voice_emotion(self, voice_emotion: Optional[str]) -> str:
        if not voice_emotion:
            return "neutral"

        v = voice_emotion.lower().strip()
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
        return mapping.get(v, v or "neutral")

    # ------------------------------------------------------
    # FLAGS DESDE CONTEXTO
    # ------------------------------------------------------
    def _update_context_flags(self, ctx: Dict[str, Any]) -> None:
        flags = self.state["context_flags"]

        # weather
        weather = ctx.get("weather", {}) or {}
        desc = (weather.get("description") or "").lower()
        flags["bad_weather"] = any(k in desc for k in ["lluvia", "tormenta", "nublado", "storm", "rain"])

        # pagos próximos
        events = ctx.get("events", []) or []
        now_iso = ctx.get("current_time_iso")
        try:
            now = datetime.fromisoformat(now_iso) if now_iso else datetime.utcnow()
        except Exception:
            now = datetime.utcnow()

        soon_count = 0
        for ev in events:
            when_str = ev.get("when")
            if not when_str:
                continue
            try:
                ev_dt = datetime.fromisoformat(when_str.replace("Z", "+00:00"))
            except Exception:
                continue

            delta_days = (ev_dt - now).total_seconds() / 86400.0
            if 0 <= delta_days <= 3:
                soon_count += 1

        flags["many_events_soon"] = soon_count >= 4

        # pagos base desde ctx["payments"]
        payments = ctx.get("payments", []) or []
        flags["many_payments_soon"] = len(payments) >= 4

        # hora del día (para energía)
        current_time = ctx.get("current_time_pretty") or ""
        # formato "HH:MM"
        try:
            hour = int((current_time.split(":")[0] or "12"))
        except Exception:
            hour = 12

        flags["morning_time"] = 5 <= hour < 12
        flags["night_time"] = hour >= 21 or hour < 5

    # ------------------------------------------------------
    # IMPACTOS SOBRE EL ESTADO
    # ------------------------------------------------------
    def _apply_text_impact(self, emo: str) -> None:
        # base
        if emo in ["sad", "worried", "angry", "tired", "mixed_tired_happy"]:
            self.state["affection"] = min(1.0, self.state["affection"] + 0.15)

        if emo == "sad":
            self.state["stress"] = min(1.0, self.state["stress"] + 0.15)
            self.state["energy"] = max(0.0, self.state["energy"] - 0.1)

        elif emo == "worried":
            self.state["stress"] = min(1.0, self.state["stress"] + 0.2)
            self.state["focus"] = max(0.0, self.state["focus"] - 0.05)

        elif emo == "angry":
            self.state["stress"] = min(1.0, self.state["stress"] + 0.25)
            self.state["focus"] = min(1.0, self.state["focus"] + 0.05)

        elif emo == "affectionate":
            self.state["affection"] = min(1.0, self.state["affection"] + 0.25)
            self.state["stress"] = max(0.0, self.state["stress"] - 0.05)

        elif emo == "happy":
            self.state["energy"] = min(1.0, self.state["energy"] + 0.15)
            self.state["stress"] = max(0.0, self.state["stress"] - 0.1)

        elif emo == "bored":
            self.state["energy"] = max(0.0, self.state["energy"] - 0.05)
            self.state["focus"] = max(0.0, self.state["focus"] - 0.05)

        elif emo == "tired":
            self.state["energy"] = max(0.0, self.state["energy"] - 0.15)
            self.state["stress"] = min(1.0, self.state["stress"] + 0.05)

        elif emo == "mixed_tired_happy":
            self.state["energy"] = max(0.0, self.state["energy"] - 0.05)
            self.state["stress"] = max(0.0, self.state["stress"] - 0.05)
            self.state["affection"] = min(1.0, self.state["affection"] + 0.1)

    def _apply_voice_impact(self, emo: str) -> None:
        """
        Por ahora, usamos etiquetas simples.
        Más adelante, esto podrá venir de un modelo acústico.
        """
        if emo == "happy":
            self.state["energy"] = min(1.0, self.state["energy"] + 0.1)
        elif emo in ["sad", "tired"]:
            self.state["energy"] = max(0.0, self.state["energy"] - 0.1)
            self.state["stress"] = min(1.0, self.state["stress"] + 0.05)
        elif emo in ["angry"]:
            self.state["stress"] = min(1.0, self.state["stress"] + 0.1)

    def _apply_context_impact(self, ctx: Dict[str, Any]) -> None:
        flags = self.state["context_flags"]

        if flags["bad_weather"]:
            # clima feo → un poco menos de energía
            self.state["energy"] = max(0.0, self.state["energy"] - 0.05)

        if flags["many_payments_soon"] or flags["many_events_soon"]:
            # muchas cosas encima → estrés
            self.state["stress"] = min(1.0, self.state["stress"] + 0.15)

        if flags["night_time"]:
            self.state["energy"] = max(0.0, self.state["energy"] - 0.1)
        elif flags["morning_time"]:
            self.state["energy"] = min(1.0, self.state["energy"] + 0.05)

        # un poco de foco extra si hay clases/exámenes
        exams = ctx.get("exams", []) or []
        classes = ctx.get("classes", []) or []
        if exams or classes:
            self.state["focus"] = min(1.0, self.state["focus"] + 0.05)

        # clamp final
        self.state["energy"] = max(0.0, min(1.0, self.state["energy"]))
        self.state["stress"] = max(0.0, min(1.0, self.state["stress"]))
        self.state["affection"] = max(0.0, min(1.0, self.state["affection"]))
        self.state["focus"] = max(0.0, min(1.0, self.state["focus"]))

    # ------------------------------------------------------
    # ESTADO GLOBAL
    # ------------------------------------------------------
    def _resolve_overall_state(self) -> str:
        """
        Decide una etiqueta final:
        - happy, affectionate, stressed, tired, empathetic, neutral, sad
        usando niveles internos + emoción de texto.
        """
        text_emo = self.state["user_emotion_text"]
        energy = self.state["energy"]
        stress = self.state["stress"]
        affection = self.state["affection"]

        # afecto alto → Auri responde en modo cariñoso
        if affection > 0.7 and text_emo in ["happy", "affectionate"]:
            return "affectionate"

        # tristeza / preocupación
        if text_emo in ["sad", "worried"]:
            return "empathetic"

        # estrés fuerte
        if stress > 0.7:
            return "stressed"

        # cansancio marcado
        if energy < 0.3:
            return "tired"

        # feliz
        if text_emo in ["happy", "mixed_tired_happy"] or energy > 0.75:
            return "happy"

        # neutro por defecto
        return "neutral"
