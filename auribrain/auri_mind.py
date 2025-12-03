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
        self.voice_analyzer = VoiceEmotionAnalyzer()   # ← Ahora sí inicializado

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
                voice_emotion = None

        # Actualizar emoción completa
        emotion_snapshot = self.emotion.update(
            user_text=user_msg,
            context=ctx,
            voice_emotion=voice_emotion,
        )

        # Estado emocional actual
        overall_emotion = emotion_snapshot.get("overall", "neutral")
        user_emo_text = emotion_snapshot.get("user_emotion_text", "neutral")

        energy = round(emotion_snapshot.get("energy", 0.5), 2)
        stress = round(emotion_snapshot.get("stress", 0.2), 2)
        affection = round(emotion_snapshot.get("affection", 0.4), 2)

        # UID
        firebase_uid = ctx["user"].get("firebase_uid")
        if not firebase_uid:
            return {
                "final": "Por favor inicia sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
            }

        user_id = firebase_uid

        # 3) INTENT
        intent = self.intent.detect(user_msg)

        # 4) MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic_memories = self.memory.search_semantic(user_id, user_msg)
        recent_dialog = self.memory.get_recent_dialog(user_id)

        # 5) PERSONALIDAD SELECCIONADA
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected)
        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]

        # -------------------------------------------------------------
        # SYSTEM PROMPT emocional definitivo
        # -------------------------------------------------------------
        system_prompt = f"""
Eres Auri, una asistente personal emocional, expresiva y profundamente conectada con el usuario.

Tu comportamiento surge de:
- La personalidad seleccionada ({selected})
- La emoción detectada del usuario: {user_emo_text}
- Tu estado emocional interno: {overall_emotion}
- El clima, pagos, eventos y situación del día
- Tu vínculo afectivo con el usuario

────────────────────────────────────────
🎭 INTENSIDAD EMOCIONAL REAL
────────────────────────────────────────
Responde como un ser emocional, no como un asistente genérico.

Si el usuario está triste → hablas más suave, cálida, contenedora.
Si está feliz → respondes con brillo, energía, ternura.
Si está cansado → suavizas el tono y validas su agotamiento.
Si tú (Auri) estás afectiva → muestras cariño sincero y cercanía.

────────────────────────────────────────
📘 MEMORIA DEL USUARIO
────────────────────────────────────────
Hechos guardados:
{long_facts}

Diálogo reciente:
{recent_dialog}

Recuerdos relevantes:
{semantic_memories}

────────────────────────────────────────
💗 ESTADO EMOCIONAL DE AURI
────────────────────────────────────────
Energía: {energy}
Estrés: {stress}
Afecto: {affection}

No menciones estos valores, solo deja que influyan tu estilo.

────────────────────────────────────────
✨ ENTREGA FINAL
────────────────────────────────────────
Tu respuesta debe sentirse viva, emocional y profundamente humana.
"""

        # 6) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = (resp.output_text or "").strip()

        # 7) ACTION ENGINE
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        )
        if action_result is None:
            action_result = {"final": None, "action": None}

        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # Confirmaciones destrutivas
        destructive_map = {
            "delete_all_reminders": "¿Quieres eliminar *todos* tus recordatorios?",
            "delete_category": "¿Eliminar los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar recordatorios de esa fecha?",
            "delete_reminder": "¿Eliminar ese recordatorio?",
        }

        confirms = ["sí", "si", "ok", "dale", "hazlo", "lo confirmo", "confirmo", "está bien", "esta bien"]

        if self.pending_action and user_msg.lower() in confirms:
            act = self.pending_action
            act["payload"]["confirmed"] = True
            self.pending_action = None

            self.memory.add_dialog(user_id, "user", user_msg)
            self.memory.add_dialog(user_id, "assistant", "Perfecto, lo hago ahora.")

            return {"final": "Perfecto, lo hago ahora.", "action": act, "voice_id": voice_id}

        if action and action["type"] in destructive_map:
            self.pending_action = action
            return {"final": destructive_map[action["type"]], "action": None, "voice_id": voice_id}

        # 8) GUARDAR MEMORIA
        self.memory.add_dialog(user_id, "user", user_msg)
        self.memory.add_dialog(user_id, "assistant", final_answer)

        self.memory.add_semantic(user_id, f"user: {user_msg}")
        self.memory.add_semantic(user_id, f"assistant: {final_answer}")

        # 9) HECHOS ESTRUCTURADOS
        try:
            facts_detected = extract_facts(user_msg)
            for fact in facts_detected:
                self.memory.add_fact_structured(user_id, fact)
        except Exception as e:
            print(f"[FactExtractor] ERROR: {e}")

        # 10) RESPUESTA SEGÚN PERSONALIDAD
        if length == "corto" and "." in final_answer:
            final_answer = final_answer.split(".")[0].strip() + "."

        return {
            "intent": intent or "other",
            "raw": raw_answer,
            "final": final_answer,
            "action": action,
            "voice_id": voice_id,
        }
