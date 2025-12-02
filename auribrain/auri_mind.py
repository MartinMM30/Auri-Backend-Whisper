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

        self.pending_action = None

    # -------------------------------------------------------------
    # THINK PIPELINE
    # -------------------------------------------------------------
    def think(self, user_msg: str):

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

        firebase_uid = ctx["user"].get("firebase_uid")
        if not firebase_uid:
            return {
                "final": "Por favor inicia sesión para activar tu memoria personal 💜",
                "intent": "auth_required",
                "voice_id": "alloy",
            }

        user_id = firebase_uid

        # 2) INTENT
        intent = self.intent.detect(user_msg)

        # 3) MEMORIA
        profile = self.memory.get_user_profile(user_id)
        long_facts = self.memory.get_facts(user_id)
        semantic_memories = self.memory.search_semantic(user_id, user_msg)
        recent_dialog = self.memory.get_recent_dialog(user_id)

        # 4) PERSONALIDAD
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS[selected]
        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]

        # 5) SYSTEM PROMPT
        system_prompt = f"""
Eres Auri, asistente personal de {profile.get("name", "usuario")}.
Tu estilo actual es: {tone} {emoji}

Memoria del usuario:
- Perfil: {profile}
- Hechos importantes: {long_facts}
- Diálogo reciente:
{recent_dialog}

Recuerdos relevantes:
{semantic_memories}

Reglas:
- Usa memoria real, no inventes datos nuevos.
- Habla con empatía.
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

        # 🔥 PARCHE: acción_result = {} siempre
        if action_result is None:
            action_result = {"final": None, "action": None}

        # Acción destructiva
        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # Confirmación
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

        facts_detected = self.extractor.extract_facts(user_msg)
        for fact in facts_detected:
            self.memory.add_fact_structured(user_id, fact)

        # 9) LIMITAR RESPUESTA SEGÚN PERSONALIDAD
        if length == "corto" and "." in final_answer:
            final_answer = final_answer.split(".")[0].strip() + "."

        # 10) 🔥 PARCHE FINAL — NUNCA devolver None
        return {
            "intent": intent or "other",
            "raw": raw_answer or "",
            "final": final_answer or "Lo siento, tuve un problema para responder 💜",
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
            print(f"⚠ No se pudo establecer usuario activo en AuriMind: {e}")
