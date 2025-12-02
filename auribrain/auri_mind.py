# auribrain/auri_mind.py

from openai import OpenAI
from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import ActionsEngine
from auribrain.entity_extractor import EntityExtractor


class AuriMind:
    """
    AuriMind V5 — Identidad estable + Confirmaciones inteligentes + Hands-Free Mode.
    """

    PERSONALITY_PRESETS = {
        "auri_classic": {"tone": "cálido y profesional", "emoji": "💜", "length": "medio", "voice_id": "alloy"},
        "soft": {"tone": "suave, calmado, relajante", "emoji": "🌙", "length": "corto", "voice_id": "nova"},
        "siri_style": {"tone": "formal, educado, preciso", "emoji": "", "length": "corto", "voice_id": "verse"},
        "anime_soft": {"tone": "tierna, expresiva y dulce", "emoji": "✨", "length": "medio", "voice_id": "hikari"},
        "professional": {"tone": "serio, empresarial", "emoji": "", "length": "medio", "voice_id": "amber"},
        "friendly": {"tone": "amigable, jovial", "emoji": "😊", "length": "medio", "voice_id": "alloy"},
        "custom_love_voice": {"tone": "dulce, afectiva, suave", "emoji": "💖", "length": "medio", "voice_id": "myGF_voice"},
    }

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine(self.client)
        self.memory = MemoryEngine()
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)

        self.personality = PersonalityEngine()
        self.response = ResponseEngine()
        self.extractor = EntityExtractor()
        self.actions = ActionsEngine()

        # Acción destructiva pendiente
        self.pending_action = None


    # -------------------------------------------------------------
    # THINK PIPELINE V5
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        raw_user_msg = user_msg.strip()
        user_msg = raw_user_msg.lower()

        if not user_msg:
            return {
                "intent": "unknown",
                "raw": "",
                "final": "No te escuché bien, ¿puedes repetirlo?",
                "action": None,
                "voice_id": "alloy",
            }

        # 0) Context
        if not self.context.is_ready():
            return {"final": "Dame un momento… estoy cargando tu información.", "intent": "wait", "raw": "", "action": None, "voice_id": "alloy"}

        # 1) Intent
        intent = self.intent.detect(user_msg)

        # 2) Context
        ctx = self.context.get_daily_context()

        # User profile
        user_name = ctx["user"].get("name", "usuario")

        # Voice preset
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])
        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]

        # 3) Build system prompt
        system_prompt = f"""
Eres Auri, asistente personal de {user_name}.
Tu estilo actual es: {tone} {emoji}.

Debes responder cálido, humano y claro.
"""

        # 4) LLM
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_user_msg},
            ],
        )
        raw_answer = resp.output_text.strip()

        # 5) Actions
        action_result = self.actions.handle(intent=intent, user_msg=user_msg, context=ctx, memory=self.memory)

        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # ==================================================
        # 🔥 COMANDOS DE VOZ PARA HANDS-FREE MODE
        # ==================================================
        if "modo manos libres" in user_msg or "hands free" in user_msg:
            if "activa" in user_msg or "enciende" in user_msg:
                return {
                    "intent": "handsfree_on",
                    "raw": raw_answer,
                    "final": "Perfecto, activé el modo manos libres.",
                    "action": {
                        "type": "set_handsfree",
                        "payload": {"enabled": True}
                    },
                    "voice_id": voice_id,
                }

            if "desactiva" in user_msg or "apaga" in user_msg:
                return {
                    "intent": "handsfree_off",
                    "raw": raw_answer,
                    "final": "Modo manos libres desactivado.",
                    "action": {
                        "type": "set_handsfree",
                        "payload": {"enabled": False}
                    },
                    "voice_id": voice_id,
                }

        # ==================================================
        # 🔥 Confirmación inteligente para acciones peligrosas
        # ==================================================
        destructive_map = {
            "delete_all_reminders": "¿Quieres que elimine *todos* tus recordatorios?",
            "delete_category": "¿Eliminar todos los recordatorios de esa categoría?",
            "delete_by_date": "¿Eliminar los recordatorios de esa fecha?",
            "delete_reminder": "¿Deseas eliminar ese recordatorio?",
            "edit_reminder": "¿Confirmas que deseas modificar ese recordatorio?",
        }

        confirm_words = ["sí", "si", "ok", "dale", "hazlo", "confirmo", "está bien", "esta bien"]

        if self.pending_action and user_msg.strip() in confirm_words:
            act = self.pending_action
            self.pending_action = None

            payload = act.get("payload", {})
            payload["confirmed"] = True
            act["payload"] = payload

            self.memory.add_interaction(user_msg=raw_user_msg, assistant_msg="Perfecto, lo hago ahora.", intent=intent)

            return {"intent": intent, "raw": raw_answer, "final": "Perfecto, lo hago ahora.", "action": act, "voice_id": voice_id}

        if action and action["type"] in destructive_map:
            self.pending_action = action
            self.memory.add_interaction(user_msg=raw_user_msg, assistant_msg=destructive_map[action["type"]], intent=intent)
            return {"intent": intent, "raw": raw_answer, "final": destructive_map[action["type"]], "action": None, "voice_id": voice_id}

        # ==================================================
        # Save memory
        # ==================================================
        self.memory.add_interaction(user_msg=raw_user_msg, assistant_msg=final_answer, intent=intent)

        # Limit length
        if length == "corto":
            final_answer = final_answer.split(".")[0].strip() + "."

        return {"intent": intent, "raw": raw_answer, "final": final_answer, "action": action, "voice_id": voice_id}
