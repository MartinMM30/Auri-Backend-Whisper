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
    AuriMind V4.5 — Identidad estable + Confirmaciones inteligentes.
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

        # 🔒 Acción pendiente para confirmación
        self.pending_action = None


    # -------------------------------------------------------------
    # THINK PIPELINE V4.5
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        user_msg = (user_msg or "").strip().lower()

        if not user_msg:
            return {
                "intent": "unknown",
                "raw": "",
                "final": "No logré escucharte bien, ¿puedes repetirlo?",
                "action": None,
                "voice_id": "alloy",
            }

        # 0) Contexto estricto
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… estoy terminando de cargar tu perfil y agenda.",
                "intent": "wait",
                "raw": "",
                "action": None,
                "voice_id": "alloy",
            }

        # 1) intención
        intent = self.intent.detect(user_msg)

        # 2) contexto completo
        ctx = self.context.get_daily_context()

        # 3) perfil del usuario
        user_name = ctx["user"].get("name") or "usuario"
        user_city = ctx["user"].get("city") or "tu ciudad"
        user_job = ctx["user"].get("occupation") or ""
        birthday = ctx["user"].get("birthday") or ""

        # 4) personalidad seleccionada
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])

        tone, emoji, length, voice_id = style["tone"], style["emoji"], style["length"], style["voice_id"]


        # 5) memoria reciente + hechos
        recent_dialog = self.memory.get_recent_dialog()
        facts = self.memory.get_facts()

        # 6) system prompt
        system_prompt = f"""
Eres Auri, asistente personal de {user_name}.
Tu estilo actual es: {tone} {emoji}.
(… se omite por longitud, igual al original …)
"""

        # 7) llamado al modelo
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        raw_answer = resp.output_text.strip()

        # 8) acciones detectadas
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory,
        )

        action = action_result.get("action")
        final_answer = action_result.get("final") or raw_answer

        # ============================================================
        # 🔒 VALIDACIÓN INTELIGENTE PARA ACCIONES DESTRUCTIVAS
        # ============================================================

        destructive_map = {
            "delete_all_reminders": "¿Quieres que elimine *todos* tus recordatorios?",
            "delete_category": "¿Confirmas que deseas eliminar todos los recordatorios de esa categoría?",
            "delete_by_date": "¿Seguro que deseas borrar todos los recordatorios de esa fecha?",
            "delete_reminder": "¿Deseas eliminar ese recordatorio?",
            "edit_reminder": "¿Confirmas que deseas modificar ese recordatorio?",
        }

        confirm_words = ["sí", "si", "ok", "dale", "hazlo", "confirmo", "está bien", "esta bien"]

        # 1) Usuario responde a un prompt de confirmación
        if self.pending_action and user_msg in confirm_words:
            act = self.pending_action
            self.pending_action = None

            # 🔐 siempre marcar confirmado
            payload = act.get("payload") or {}
            payload["confirmed"] = True
            act["payload"] = payload

            return {
                "intent": intent,
                "raw": raw_answer,
                "final": "Perfecto, lo hago ahora.",
                "action": act,  # ahora sí ejecutamos
                "voice_id": voice_id,
            }

        # 2) Acción peligrosa recién detectada
        if action and action["type"] in destructive_map:

            # Caso: usuario ya dijo explícitamente "elimínalos ya"
            if "ya" in user_msg or "de inmediato" in user_msg:
                payload = action.get("payload") or {}
                payload["confirmed"] = True
                action["payload"] = payload
                return {
                    "intent": intent,
                    "raw": raw_answer,
                    "final": "De acuerdo, lo hago ahora mismo.",
                    "action": action,
                    "voice_id": voice_id,
                }

            # Pedir confirmación
            self.pending_action = action
            return {
                "intent": intent,
                "raw": raw_answer,
                "final": destructive_map[action["type"]],
                "action": None,
                "voice_id": voice_id,
            }

        # ============================================================
        # FIN DE VALIDACIÓN DE ACCIONES
        # ============================================================

        # 9) límite por personalidad
        if length == "corto":
            final_answer = final_answer.split(".")[0].strip() + "."

        # 10) guardar memoria
        self.memory.add_interaction(
            user_msg=user_msg,
            assistant_msg=final_answer,
            intent=intent,
        )

        # 11) retorno final
        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action,
            "voice_id": voice_id,
        }
