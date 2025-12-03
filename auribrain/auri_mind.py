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

        # Módulos especiales
        self.crisis = CrisisEngine()
        self.sleep = SleepEngine()
        self.love = LoveModeEngine()
        self.energy_mode = EnergyEngine()
        self.slang = SlangModeEngine()
        self.focus = FocusEngine()  # usado como modo también
        self.journal = JournalEngine()
        self.mental = MentalHealthEngine()
        self.routines = RoutineEngine()
        self.weather_advice = WeatherAdviceEngine()

        self.pending_action = None

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str, pcm_audio: bytes = None):

        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {
                "final": "No escuché nada, ¿podés repetirlo?",
                "intent": "unknown",
                "voice_id": "alloy",
            }

        # 1) CONTEXTO
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… sigo preparando tu pantalla y tu perfil 💜",
                "intent": "wait",
                "voice_id": "alloy",
            }

        ctx = self.context.get_daily_context()

        # -------------------------------------------------------------
        # 2) EMOCIÓN DESDE VOZ (si existe audio)
        # -------------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception as e:
                print(f"[VoiceEmotion] ERROR: {e}")

        # 3) EMOCIÓN COMPLETA (texto + contexto + voz)
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall_emotion = emotion_snapshot.get("overall", "neutral")
        user_emo_text = emotion_snapshot.get("user_emotion_text", "neutral")
        energy = float(emotion_snapshot.get("energy", 0.5))
        stress = float(emotion_snapshot.get("stress", 0.2))
        affection = float(emotion_snapshot.get("affection", 0.4))

        # 4) UID
        user_info = ctx.get("user") or {}
        firebase_uid = user_info.get("firebase_uid")

        if not firebase_uid:
            return {
                "final": "Por favor iniciá sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
            }

        user_id = firebase_uid
        txt = user_msg.lower()

        # =============================================================
        # 🔥 PRIORIDAD MÁXIMA: CRISIS
        # =============================================================
        if self.crisis.detect(user_msg, emotion_snapshot):
            final = self.crisis.respond(user_info.get("name"))
            self.memory.add_semantic(user_id, f"[crisis_detected] {user_msg}")
            return {
                "final": final,
                "raw": final,
                "intent": "conversation.general",
                "action": None,
                "voice_id": "alloy",
            }

        # =============================================================
        # 🔥 MODOS ESPECIALES — antes del LLM
        # =============================================================

        # Modo Sueño
        if self.sleep.detect(txt, overall_emotion, ctx):
            final = self.sleep.respond(ctx, overall_emotion)
            return {"final": final, "raw": final, "intent": "conversation.general", "action": None, "voice_id": "alloy"}

        # Modo Pareja
        if self.love.detect(txt, affection):
            final = self.love.respond(ctx)
            self.memory.add_semantic(user_id, "[love_mode_triggered]")
            return {
                "final": final,
                "raw": final,
                "intent": "conversation.general",
                "action": None,
                "voice_id": "myGF_voice",
            }

        # Modo Slang / Humor Negro
        slang = self.slang.detect(txt, stress)
        if slang:
            final = self.slang.respond(slang)
            return {"final": final, "raw": final, "intent": "conversation.general", "action": None, "voice_id": "alloy"}

        # Modo Focus
        if self.focus.detect(txt):
            final = self.focus.respond(ctx)
            return {"final": final, "raw": final, "intent": "focus", "action": None, "voice_id": "alloy"}

        # Modo Energía
        energy_mode = self.energy_mode.detect(txt, energy)
        if energy_mode:
            final = self.energy_mode.respond(energy_mode, ctx)
            return {"final": final, "raw": final, "intent": "energy", "action": None, "voice_id": "alloy"}

        # Modo Salud Mental
        if self.mental.detect(txt, stress):
            final = self.mental.respond()
            return {"final": final, "raw": final, "intent": "mental_health", "action": None, "voice_id": "alloy"}

        # Modo Rutinas
        if any(k in txt for k in ["rutina", "organizar", "ordenar", "mi día", "mi dia"]):
            mode = self.routines.detect(ctx, emotion_snapshot)
            if mode:
                final = self.routines.respond(mode)
                return {"final": final, "raw": final, "intent": "routine", "action": None, "voice_id": "alloy"}

        # Modo clima / outfit
        if any(k in txt for k in ["clima", "tiempo", "ropa", "outfit", "frio", "calor", "lluvia"]):
            wmode = self.weather_advice.detect(ctx)
            if wmode:
                final = self.weather_advice.respond(wmode)
                return {"final": final, "raw": final, "intent": "weather", "action": None, "voice_id": "alloy"}

        # Journal automático
        if self.journal.detect(user_msg, emotion_snapshot):
            entry = self.journal.generate_entry(user_msg, emotion_snapshot)
            self.memory.add_semantic(user_id, entry)

        # =============================================================
        # 🔵 INTENT NORMAL
        # =============================================================
        intent = self.intent.detect(user_msg)

        # MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic = self.memory.search_semantic(user_id, user_msg)
        recent = self.memory.get_recent_dialog(user_id)

        # PERSONALIDAD
        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # =============================================================
        # SYSTEM PROMPT
        # =============================================================

        system_prompt = f"""
Eres Auri, una asistente emocional, expresiva y profundamente conectada con el usuario.

Personalidad actual: {selected} ({tone} {emoji})
Emoción del usuario (texto): {user_emo_text}
Emoción del usuario (voz): {voice_emotion}
Estado emocional interno: {overall_emotion}

Recuerdos reales:
{long_facts}

Diálogo reciente:
{recent}

Memoria semántica relevante:
{semantic}

Responde como un ser cálido, vivo, humano y emocional.
"""

        # =============================================================
        # LLM
        # =============================================================
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )
        raw_answer = (resp.output_text or "").strip()

        # ACCIONES
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        )

        if action_result is None:
            action_result = {"final": None, "action": None}

        final = action_result.get("final") or raw_answer
        action = action_result.get("action")

        # CONFIRMACIONES DESTRUCTIVAS
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
                "action": act,
                "voice_id": voice_id,
            }

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            return {"final": destructive_map[action["type"]], "action": None, "voice_id": voice_id}

        # GUARDAR MEMORIA
        self.memory.add_dialog(user_id, "user", user_msg)
        self.memory.add_dialog(user_id, "assistant", final)
        self.memory.add_semantic(user_id, f"user: {user_msg}")
        self.memory.add_semantic(user_id, f"assistant: {final}")

        # HECHOS
        try:
            facts = extract_facts(user_msg)
            for f in facts:
                self.memory.add_fact_structured(user_id, f)
        except:
            pass

        # RESPUESTA CORTA
        if length == "corto" and "." in final:
            final = final.split(".")[0] + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final,
            "action": action,
            "voice_id": voice_id,
        }

    # -------------------------------------------------------------
    # UID DESDE WS
    # -------------------------------------------------------------
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


# Compatibilidad con código anterior
AuriMindV6 = AuriMindV7
