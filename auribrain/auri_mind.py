# auribrain/auri_mind.py

from openai import OpenAI

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

# 🔥 NUEVOS MÓDULOS
from auribrain.sleep_engine import SleepEngine
from auribrain.energy_engine import EnergyEngine
from auribrain.love_mode_engine import LoveModeEngine


class AuriMindV6:

    PERSONALITY_PRESETS = {
        "auri_classic": {"tone": "cálido y profesional", "emoji": "💜", "length": "medio", "voice_id": "alloy"},
        "soft": {"tone": "suave y calmado", "emoji": "🌙", "length": "corto", "voice_id": "nova"},
        "siri_style": {"tone": "formal, educado", "emoji": "", "length": "corto", "voice_id": "verse"},
        "anime_soft": {"tone": "dulce y expresiva", "emoji": "✨", "length": "medio", "voice_id": "hikari"},
        "professional": {"tone": "serio", "emoji": "", "length": "medio", "voice_id": "amber"},
        "friendly": {"tone": "amigable", "emoji": "😊", "length": "medio", "voice_id": "alloy"},
        "custom_love_voice": {"tone": "afectiva y suave", "emoji": "💖", "length": "medio", "voice_id": "myGF_voice"},
    }

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine(self.client)
        self.memory = MemoryOrchestrator()
        self.context = ContextEngine()
        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()
        self.emotion = EmotionEngine()
        self.voice_analyzer = VoiceEmotionAnalyzer()

        # 🔥 Nuevos motores
        self.sleep = SleepEngine()
        self.energy = EnergyEngine()
        self.love = LoveModeEngine()

        self.pending_action = None

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str, pcm_audio: bytes = None):

        user_msg = (user_msg or "").strip()
        if not user_msg:
            return {"final": "No escuché nada, ¿puedes repetirlo?", "intent": "unknown", "voice_id": "alloy"}

        # 1) CONTEXTO
        if not self.context.is_ready():
            return {"final": "Dame un momento… sigo preparando tu pantalla y tu perfil 💜", "intent": "wait", "voice_id": "alloy"}

        ctx = self.context.get_daily_context()

        # -------------------------------------------------------------
        # 2) EMOCIÓN POR VOZ
        # -------------------------------------------------------------
        voice_emotion = None
        if pcm_audio:
            try:
                voice_emotion = self.voice_analyzer.analyze(pcm_audio)
            except Exception as e:
                print(f"[VoiceEmotion ERROR]: {e}")

        # 3) EMOCIÓN COMPLETA
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        overall_emotion = emotion_snapshot.get("overall", "neutral")
        user_emo_text = emotion_snapshot.get("user_emotion_text", "neutral")
        energy = round(emotion_snapshot.get("energy", 0.5), 2)
        stress = round(emotion_snapshot.get("stress", 0.2), 2)
        affection = round(emotion_snapshot.get("affection", 0.4), 2)

        # 4) USER ID
        user_info = ctx.get("user") or {}
        firebase_uid = user_info.get("firebase_uid")
        if not firebase_uid:
            return {"final": "Por favor inicia sesión para activar tu memoria personal 💜", "intent": "auth_required", "voice_id": "alloy"}

        user_id = firebase_uid

        # 5) INTENT
        intent = self.intent.detect(user_msg)

        # 6) MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic_memories = self.memory.search_semantic(user_id, user_msg)
        recent_dialog = self.memory.get_recent_dialog(user_id)

        # ================================================================
        # 🔥🔥 MODO CRISIS (PRIORIDAD MÁXIMA)
        # ================================================================
        crisis = self.emotion.detect_crisis(user_msg, emotion_snapshot)
        if crisis:
            return {
                "final": self.emotion.respond_crisis(context=ctx, emotion_state=emotion_snapshot),
                "intent": "crisis",
                "voice_id": "alloy",
            }

        # ================================================================
        # 🌙 1. MODO SUEÑO
        # ================================================================
        txt = user_msg.lower()
        emotion_state = overall_emotion

        if self.sleep.detect(txt, emotion_state):
            return {
                "final": self.sleep.respond(ctx, emotion_state),
                "intent": "sleep_mode",
                "voice_id": "alloy",
            }

        # ================================================================
        # 💖 2. MODO PAREJA / AMOR
        # ================================================================
        if self.love.detect(txt, affection):
            return {
                "final": self.love.respond(ctx),
                "intent": "love_mode",
                "voice_id": "myGF_voice" if "love" in ctx.get("prefs", {}).get("personality", "") else "alloy",
            }

        # ================================================================
        # ⚡ 3. MODO ENERGÍA (MOTIVACIÓN / RECARGA)
        # ================================================================
        energy_mode = self.energy.detect(txt, energy)
        if energy_mode:
            return {
                "final": self.energy.respond(energy_mode, ctx),
                "intent": f"energy_{energy_mode}",
                "voice_id": "alloy",
            }

        # 7) PERSONALIDAD
        prefs = ctx.get("prefs", {}) or {}
        selected = prefs.get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])
        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]

        # -------------------------------------------------------------
        # SYSTEM PROMPT PRINCIPAL
        # -------------------------------------------------------------
        system_prompt = f"""
Eres Auri, una asistente personal emocional y viva.

Tu estilo depende de:
- Personalidad seleccionada: {selected} ({tone} {emoji})
- Emoción del usuario: {user_emo_text}
- Emoción por voz: {voice_emotion}
- Estado emocional interno: {overall_emotion}
- Energía: {energy}, Estrés: {stress}, Afecto: {affection}
- Objeto semántico del día (clima, pagos, agenda)
- Memoria real del usuario

Responde con calidez, humanidad y sinceridad. Nunca suenes robótica.
Solo usa la información real mostrada en memoria.
"""

        # 8) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # 9) ACTION ENGINE
        action_result = self.actions.handle(intent=intent, user_msg=user_msg, context=ctx, memory=self.memory)
        if not action_result:
            action_result = {"final": None, "action": None}

        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # -------------------------------------------------------------
        # Confirmaciones destructivas
        # -------------------------------------------------------------
        destructive_map = {
            "delete_all_reminders": "¿Quieres eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
            "edit_reminder": "¿Modificar ese recordatorio?",
        }

        confirms = ["sí", "si", "ok", "dale", "hazlo", "lo confirmo", "confirmo", "está bien", "esta bien"]

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None
            return {"final": "Perfecto, lo hago ahora.", "action": act, "voice_id": voice_id}

        if action and action.get("type") in destructive_map:
            self.pending_action = action
            return {"final": destructive_map[action["type"]], "action": None, "voice_id": voice_id}

        # -------------------------------------------------------------
        # Guardar memoria
        # -------------------------------------------------------------
        self.memory.add_dialog(user_id, "user", user_msg)
        self.memory.add_dialog(user_id, "assistant", final_answer)

        self.memory.add_semantic(user_id, f"user: {user_msg}")
        self.memory.add_semantic(user_id, f"assistant: {final_answer}")
        self.memory.add_semantic(user_id, f"auri_mood: {overall_emotion}")

        try:
            for fact in extract_facts(user_msg):
                self.memory.add_fact_structured(user_id, fact)
        except Exception as e:
            print("[FactExtractor] ERROR:", e)

        if length == "corto" and "." in final_answer:
            final_answer = final_answer.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action,
            "voice_id": voice_id,
        }

    # -------------------------------------------------------------
    # UID desde WebSocket
    # -------------------------------------------------------------
    def set_user_uid(self, uid: str):
        if not uid:
            return
        try:
            self.context.set_user_uid(uid)
            self.memory.get_user_profile(uid)
            self.memory.get_recent_dialog(uid)
            print("UID detectado por AuriMind:", uid)
        except Exception as e:
            print("⚠ No se pudo registrar UID:", e)
