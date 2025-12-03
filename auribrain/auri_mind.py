# auribrain/auri_mind.py

from openai import OpenAI

# Motores base
from auribrain.intent_engine import IntentEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import ActionsEngine
from auribrain.entity_extractor import EntityExtractor
from auribrain.memory_orchestrator import MemoryOrchestrator
from auribrain.fact_extractor import extract_facts
from auribrain.emotion_engine import EmotionEngine
from auribrain.voice_emotion_analyzer import VoiceEmotionAnalyzer

# Modos especiales (archivos separados)
from auribrain.crisis_engine import CrisisEngine
from auribrain.focus_engine import FocusEngine
from auribrain.sleep_engine import SleepEngine
from auribrain.love_mode_engine import LoveModeEngine
from auribrain.energy_engine import EnergyEngine
from auribrain.slang_mode_engine import SlangModeEngine
from auribrain.journal_engine import JournalEngine
from auribrain.mental_health_engine import MentalHealthEngine
from auribrain.routine_engine import RoutineEngine
from auribrain.weather_advice_engine import WeatherAdviceEngine


# ============================================================
# AURI MIND V7 — Motor emocional + modos inteligentes
# ============================================================

class AuriMindV7:

    PERSONALITY_PRESETS = {
        "auri_classic": {
            "tone": "cálido y profesional",
            "emoji": "💜",
            "length": "medio",
            "voice_id": "alloy",
        },
        "soft": {
            "tone": "suave y calmado",
            "emoji": "🌙",
            "length": "corto",
            "voice_id": "nova",
        },
        "siri_style": {
            "tone": "formal, educado",
            "emoji": "",
            "length": "corto",
            "voice_id": "verse",
        },
        "anime_soft": {
            "tone": "dulce y expresiva",
            "emoji": "✨",
            "length": "medio",
            "voice_id": "hikari",
        },
        "professional": {
            "tone": "serio",
            "emoji": "",
            "length": "medio",
            "voice_id": "amber",
        },
        "friendly": {
            "tone": "amigable",
            "emoji": "😊",
            "length": "medio",
            "voice_id": "alloy",
        },
        "custom_love_voice": {
            "tone": "afectiva y suave",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        },
    }

    def __init__(self):
        self.client = OpenAI()

        # Motores principales
        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # Modos especiales
        self.crisis = CrisisEngine()
        self.sleep = SleepEngine()
        self.love = LoveModeEngine()
        self.energy_mode = EnergyEngine()
        self.slang = SlangModeEngine()
        self.focus = FocusEngine()
        self.journal = JournalEngine()
        self.mental = MentalHealthEngine()
        self.routines = RoutineEngine()
        self.weather_advice = WeatherAdviceEngine()

        # Perfil lingüístico adaptativo para humor / slang
        self.slang_profile = {}

        # Acción pendiente (confirmaciones destructivas)
        self.pending_action = None

    # ---------------------------------------------------------
    # Helper: detectar si es una PREGUNTA DIRECTA
    # (para NO disparar modos automáticos antes del LLM)
    # ---------------------------------------------------------
    def _is_direct_question(self, text: str) -> bool:
        if not text:
            return False

        t = text.lower().strip()

        # Pregunta explícita
        if "?" in t:
            return True

        QUESTION_STARTS = [
            "qué ", "que ",
            "cómo ", "como ",
            "cuándo", "cuando",
            "dónde", "donde",
            "por qué", "porque",
            "quién", "quien",
            "cuál", "cual",
            "what", "how", "why", "who", "when",
            "dime", "decime", "explícame",
            "enséñame", "enseñame",
        ]

        return any(t.startswith(q) for q in QUESTION_STARTS)


    # ---------------------------------------------------------
    # THINK PIPELINE
    # ---------------------------------------------------------
    def think(self, user_msg: str, pcm_audio: bytes = None):

        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {
                "final": "No escuché nada, ¿podés repetirlo?",
                "intent": "unknown",
                "voice_id": "alloy",
                "action": None,
            }

        # 1) CONTEXTO
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… sigo preparando tu pantalla y tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
                "action": None,
            }

        ctx = self.context.get_daily_context()
        txt = user_msg.lower()

        # ¿Es una pregunta directa? → evitar modos automáticos
        
        skip_special_modes = self._is_direct_question(user_msg)

# Bloquear TODOS los modos si es una petición de traducción / aprendizaje
        TRANSLATION_TRIGGERS = [
            "cómo se dice", "como se dice",
            "dime qué significa", "que significa",
            "dime cómo decir", "como decir",
            "traduce", "traducción", "translate",
            "hola en", "cómo digo", "como digo",
        ]

        if any(t in txt for t in TRANSLATION_TRIGGERS):
            skip_special_modes = True


        # ---------------------------------------------------------
        # 2) EMOCIÓN DESDE VOZ (si hay audio)
        # ---------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception as e:
                print(f"[VoiceEmotion] ERROR: {e}")

        # ---------------------------------------------------------
        # 3) EMOCIÓN TOTAL
        # ---------------------------------------------------------
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall = emotion_snapshot.get("overall", "neutral")
        user_emo_text = emotion_snapshot.get("user_emotion_text", "neutral")
        energy = float(emotion_snapshot.get("energy", 0.5))
        stress = float(emotion_snapshot.get("stress", 0.2))
        affection = float(emotion_snapshot.get("affection", 0.4))

        # ---------------------------------------------------------
        # 4) UID
        # ---------------------------------------------------------
        user_info = ctx.get("user", {}) or {}
        uid = user_info.get("firebase_uid")

        if not uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
                "action": None,
            }

        # =========================================================
        # 🔥 PRIORIDAD MÁXIMA: CRISIS
        # =========================================================
        if self.crisis.detect(user_msg, emotion_snapshot):
            msg = self.crisis.respond(user_info.get("name"))
            self.memory.add_semantic(uid, f"[crisis_detected] {user_msg}")
            return {
                "final": msg,
                "raw": msg,
                "intent": "crisis",
                "voice_id": "alloy",
                "action": None,
            }

        # =========================================================
        # 🔥 MODOS ANTES DEL LLM (SOLO SI NO ES PREGUNTA DIRECTA)
        # =========================================================

        # Modo Sueño
        if not skip_special_modes and self.sleep.detect(txt, overall, ctx):
            msg = self.sleep.respond(ctx, overall)
            return {
                "final": msg,
                "raw": msg,
                "intent": "sleep",
                "voice_id": "alloy",
                "action": None,
            }

        # Modo Pareja / Amor
        if not skip_special_modes and self.love.detect(txt, affection):
            msg = self.love.respond(ctx)
            self.memory.add_semantic(uid, "[love_mode_triggered]")
            return {
                "final": msg,
                "raw": msg,
                "intent": "love",
                "voice_id": "myGF_voice",
                "action": None,
            }

        # Modo Humor / Slang / Regional adaptativo
        slang_mode = None
        if not skip_special_modes:
            slang_mode = self.slang.detect(txt, self.slang_profile)

        if slang_mode:
            msg = self.slang.respond(slang_mode, self.slang_profile)
            return {
                "final": msg,
                "raw": msg,
                "intent": "slang",
                "voice_id": "alloy",
                "action": None,
            }

        # Modo Focus
        if not skip_special_modes and self.focus.detect(txt):
            msg = self.focus.respond(ctx)
            return {
                "final": msg,
                "raw": msg,
                "intent": "focus",
                "voice_id": "alloy",
                "action": None,
            }

        # Modo Energía
        energy_mode = None
        if not skip_special_modes:
            if not any(word in txt for word in ["dime", "hola en", "cómo se dice", "traduce"]):
                energy_mode = self.energy_mode.detect(txt, energy)

        if energy_mode:
            msg = self.energy_mode.respond(energy_mode, ctx)
            return {
                "final": msg,
                "raw": msg,
                "intent": "energy",
                "voice_id": "alloy",
                "action": None,
            }

        # Salud Mental leve
        if not skip_special_modes and self.mental.detect(txt, stress):
            msg = self.mental.respond()
            return {
                "final": msg,
                "raw": msg,
                "intent": "mental_health",
                "voice_id": "alloy",
                "action": None,
            }

        # Rutinas Inteligentes
        if (
            not skip_special_modes
            and any(k in txt for k in ["rutina", "organizar", "ordenar", "mi día", "mi dia"])
        ):
            rmode = self.routines.detect(ctx, emotion_snapshot)
            if rmode:
                msg = self.routines.respond(rmode)
                return {
                    "final": msg,
                    "raw": msg,
                    "intent": "routine",
                    "voice_id": "alloy",
                    "action": None,
                }

        # Consejos por clima / outfit
        if not skip_special_modes and any(
            k in txt for k in ["clima", "tiempo", "ropa", "outfit", "frio", "calor", "lluvia"]
        ):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                msg = self.weather_advice.respond(wmode)
                return {
                    "final": msg,
                    "raw": msg,
                    "intent": "weather",
                    "voice_id": "alloy",
                    "action": None,
                }

        # Journal automático (no cambia la respuesta, solo guarda)
        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(uid, entry)

        # =========================================================
        # 5) INTENT NORMAL + LLM
        # =========================================================
        intent = self.intent.detect(user_msg)

        # MEMORIA REAL
        profile = self.memory.get_user_profile(uid)
        long_facts = self.memory.get_facts(uid)
        semantic = self.memory.search_semantic(uid, user_msg)
        recent = self.memory.get_recent_dialog(uid)

        # PERSONALIDAD ACTUAL
        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(
            selected,
            self.PERSONALITY_PRESETS["auri_classic"],
        )

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # ---------------------------------------------------------
        # SYSTEM PROMPT
        # ---------------------------------------------------------
        system_prompt = f"""
Eres Auri, una asistente emocional, expresiva y profundamente conectada con el usuario.

Personalidad: {selected} ({tone} {emoji})
Emoción del usuario (texto): {user_emo_text}
Emoción del usuario (voz): {voice_emotion}
Estado interno de Auri: {overall}

Perfil del usuario:
{profile}

Hechos duraderos:
{long_facts}

Diálogo reciente:
{recent}

Memoria relevante:
{semantic}

Responde como un ser cálido, humano y emocional.
Adáptate a su estado emocional y a tu personalidad actual.
"""

        # ---------------------------------------------------------
        # LLM
        # ---------------------------------------------------------
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # ---------------------------------------------------------
        # ACCIONES (recordatorios, etc.)
        # ---------------------------------------------------------
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        ) or {"final": None, "action": None}

        final = action_result.get("final") or raw_answer
        action = action_result.get("action")

        # ---------------------------------------------------------
        # CONFIRMACIONES DESTRUCTIVAS
        # ---------------------------------------------------------
        destructive_map = {
            "delete_all_reminders": "¿Querés eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
        }

        confirms = ["sí", "si", "ok", "dale", "hazlo", "confirmo"]

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None
            return {
                "final": "Perfecto, lo hago ahora 💜",
                "raw": "Perfecto, lo hago ahora 💜",
                "intent": intent,
                "voice_id": voice_id,
                "action": act,
            }

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            return {
                "final": destructive_map[action["type"]],
                "raw": destructive_map[action["type"]],
                "intent": intent,
                "voice_id": voice_id,
                "action": None,
            }

        # ---------------------------------------------------------
        # GUARDAR MEMORIA REAL
        # ---------------------------------------------------------
        self.memory.add_dialog(uid, "user", user_msg)
        self.memory.add_dialog(uid, "assistant", final)
        self.memory.add_semantic(uid, f"user: {user_msg}")
        self.memory.add_semantic(uid, f"assistant: {final}")

        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(uid, fact)
        except Exception as e:
            print(f"[FactExtractor] ERROR: {e}")

        # RESPUESTA CORTA SI PERSONALIDAD = corto
        if length == "corto" and "." in final:
            final = final.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final,
            "action": action,
            "voice_id": voice_id,
        }

    # ---------------------------------------------------------
    # UID DESDE WS
    # ---------------------------------------------------------
    def set_user_uid(self, uid: str):
        if not uid:
            return
        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_facts(uid)
            self.memory.get_recent_dialog(uid)
            print(f"UID detectado por AuriMind: {uid}")
        except Exception as e:
            print(f"[AuriMind] ERROR al establecer UID: {e}")


# Compatibilidad con código antiguo
AuriMindV6 = AuriMindV7
