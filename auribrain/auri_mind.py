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
    Núcleo de inteligencia de Auri — Versión V3 (CON CONTEXTO REAL)
    """

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
    # THINK — pipeline moderno
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

        # 1) memoria
        self.memory.add_interaction(user_msg)

        # 2) intención
        intent = self.intent.detect(user_msg)

        # 3) CONTEXTO REAL
        ctx = self.context.get_daily_context()

        # 4) personalidad dinámica
        style = self.personality.build_final_style(context=ctx, emotion=self.memory.get_emotion())
        tone = style["tone"]

        # ---------------------------------------------------------
        # CONTEXTO PARA EL PROMPT (nuevo)
        # ---------------------------------------------------------
        ctx_prompt = (
            f"Nombre del usuario: {ctx['user'].get('name')}\n"
            f"Ciudad: {ctx['user'].get('city')}\n"
            f"Clima: {ctx['weather'].get('temp')}°C, {ctx['weather'].get('description')}\n"
            f"Eventos del día: {ctx['events']}\n"
            f"Pagos pendientes: {ctx['bills']}\n"
            f"Preferencias: {ctx['prefs']}\n"
        )

        # ---------------------------------------------------------
        # 5) SYSTEM PROMPT
        # ---------------------------------------------------------
        system_prompt = (
            "Eres Auri, un asistente personal cálido, humano y cercano. "
            f"Habla en un tono {tone}. "
            "Responde siempre en 1 o 2 frases. "
            "Nunca menciones tu proceso interno ni tu análisis. "
            "Usa el contexto si es útil.\n\n"
            f"--- CONTEXTO DEL USUARIO ---\n{ctx_prompt}\n"
            "-----------------------------\n"
        )

        # 6) LLM REQUEST
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # 7) Acciones
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory
        )

        final_answer = action_result.get("final") or raw_answer

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action_result.get("action")
        }
