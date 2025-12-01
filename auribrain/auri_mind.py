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
        },
        "soft": {
            "tone": "suave, calmado, relajante",
            "emoji": "🌙",
            "length": "corto",
        },
        "siri_style": {
            "tone": "formal, educado, preciso",
            "emoji": "",
            "length": "corto",
        },
        "anime_soft": {
            "tone": "tierna, expresiva y dulce",
            "emoji": "✨",
            "length": "medio",
        },
        "professional": {
            "tone": "serio, claro, empresarial",
            "emoji": "",
            "length": "medio",
        },
        "friendly": {
            "tone": "amigable, casual, cercano",
            "emoji": "😊",
            "length": "medio",
        },
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
                "action": None
            }

        # 0) Contexto estricto
        if not self.context.is_ready():
            return {
                "final": "Dame un momento… estoy terminando de cargar tu perfil y agenda.",
                "intent": "wait",
                "raw": "",
                "action": None
            }

        # 1) memoria a corto plazo
        self.memory.add_interaction(user_msg)

        # 2) intención
        intent = self.intent.detect(user_msg)

        # 3) contexto completo
        ctx = self.context.get_daily_context()

        # 4) perfil del usuario
        user_name = ctx["user"].get("name") or "usuario"
        user_city = ctx["user"].get("city") or "tu ciudad"
        user_job = ctx["user"].get("occupation") or ""
        birthday = ctx["user"].get("birthday") or ""

        # 5) personalidad seleccionada
        selected = ctx["prefs"].get("personality", "auri_classic")
        style = self.PERSONALITY_PRESETS.get(selected, self.PERSONALITY_PRESETS["auri_classic"])

        tone = style["tone"]
        emoji = style["emoji"]
        length = style["length"]

        # 6) system prompt V4
        system_prompt = f"""
Eres Auri, asistente personal de {user_name}.
Tu estilo actual es: {tone} {emoji}.

IDENTIDAD:
- Nombre del usuario: {user_name}
- Ciudad: {user_city}
- Ocupación: {user_job}
- Cumpleaños: {birthday}

CLIMA ACTUAL:
{ctx["weather"]}

AGENDA:
{ctx["events"]}

PREFERENCIAS:
{ctx["prefs"]}

REGLAS IMPORTANTES:
- Si el usuario pregunta “¿quién soy?”, responde literalmente: "{user_name}".
- Usa clima, ciudad, cumpleaños, clases, pagos y eventos si aplican.
- Si la personalidad indica “corto”, responde en 1 sola frase.
- Si la personalidad indica “medio”, responde en 1–2 frases naturales.
- Mantén un estilo humano, cálido y claro.
"""

        # 7) llamada al modelo
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # 8) acciones (recordatorios, pagos, cumpleaños, ciudad…)
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory
        )

        final_answer = action_result.get("final") or raw_answer

        # 9) límite de longitud por personalidad
        if length == "corto":
            final_answer = final_answer.split(".")[0].strip() + "."

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action_result.get("action")
        }
