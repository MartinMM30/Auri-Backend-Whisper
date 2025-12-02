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
    AuriMind V4 — Identidad estable, contexto completo, personalidad dinámica.
    """

    PERSONALITY_PRESETS = {
        "auri_classic": {
            "tone": "cálido y profesional",
            "emoji": "💜",
            "length": "medio",
            "voice_id": "alloy",
        },
        "soft": {
            "tone": "suave, calmado, relajante",
            "emoji": "🌙",
            "length": "corto",
            "voice_id": "nova",
        },
        "siri_style": {
            "tone": "formal, educado, preciso",
            "emoji": "",
            "length": "corto",
            "voice_id": "verse",
        },
        "anime_soft": {
            "tone": "tierna, expresiva y dulce",
            "emoji": "✨",
            "length": "medio",
            "voice_id": "hikari",
        },
        "professional": {
            "tone": "serio, empresarial",
            "emoji": "",
            "length": "medio",
            "voice_id": "amber",
        },
        "friendly": {
            "tone": "amigable, jovial",
            "emoji": "😊",
            "length": "medio",
            "voice_id": "alloy",
        },
        "custom_love_voice": {
            "tone": "dulce, afectiva, suave",
            "emoji": "💖",
            "length": "medio",
            "voice_id": "myGF_voice",
        }
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

    # -------------------------------------------------------------
    # THINK PIPELINE V4
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        user_msg = (user_msg or "").strip()

        if not user_msg:
            return {
                "intent": "unknown",
                "raw": "",
                "final": "No logré escucharte bien, ¿puedes repetirlo?",
                "action": None,
                "voice_id": "alloy"
            }

        # Esperar contexto
        if not self.context.is_ready():
            return {
                "intent": "wait",
                "raw": "",
                "final": "Dame un momento… estoy terminando de cargar tu perfil y agenda.",
                "action": None,
                "voice_id": "alloy"
            }

        # Memoria a corto plazo
        self.memory.add_interaction(user_msg)

        # Detectar intención
        intent = self.intent.detect(user_msg)

        # Obtener contexto actual
        ctx = self.context.get_daily_context()

        # Perfil del usuario
        user = ctx.get("user", {})
        user_name = user.get("name", "usuario")
        user_city = user.get("city", "tu ciudad")
        user_job = user.get("occupation", "")
        birthday = user.get("birthday", "")

        # Personalidad configurada
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(
            selected,
            self.PERSONALITY_PRESETS["auri_classic"]
        )

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]
        voice_id = style["voice_id"]

        # SYSTEM PROMPT
        system_prompt = f"""
Eres Auri, asistente personal de {user_name}.
Tu estilo actual es: {tone} {emoji}.

IDENTIDAD DEL USUARIO:
- Nombre: {user_name}
- Ciudad: {user_city}
- Ocupación: {user_job}
- Cumpleaños: {birthday}

INFORMACIÓN EN TIEMPO REAL:
- Zona horaria: {ctx.get('timezone')}
- Hora local: {ctx.get('current_time_pretty')}
- Fecha: {ctx.get('current_date_pretty')}
- ISO: {ctx.get('current_time_iso')}

REGLAS:
- Si pregunta la hora → usa la hora local.
- Si pregunta la fecha → usa la fecha local.
- Si pregunta quién es → responde exactamente: "{user_name}".
- Usa un estilo humano, cálido, natural.
"""

        # ---------------------------
        # RESPUESTA BASE CON LLM
        # ---------------------------
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # ---------------------------
        # PROCESAR ACCIONES
        # ---------------------------
        action_res = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory
        )

        final_answer = action_res.get("final") or raw_answer
        action = action_res.get("action")

        # Limitar longitud si personalidad lo pide
        if length == "corto":
            final_answer = final_answer.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action,
            "voice_id": voice_id
        }
