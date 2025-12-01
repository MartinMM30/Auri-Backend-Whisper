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
    Núcleo de inteligencia de Auri — Versión V3
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

        # 1) memorizar
        self.memory.add_interaction(user_msg)

        # 2) detectar intención
        intent = self.intent.detect(user_msg)

        # 3) obtener contexto completo
        ctx = self.context.get_daily_context()

        # 4) personalidad final dinámica
        personality_style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        tone = personality_style["tone"]

        # 5) system prompt
        system_prompt = (
            "Eres Auri, un asistente personal avanzado, natural y cercano. "
            "Responde SIEMPRE en 1 o 2 frases como un humano real. "
            "No menciones tus procesos, emociones internas o análisis. "
            "No digas que estás pensando o procesando algo. "
            "No repitas lo que dice el usuario. "
            f"Habla con un tono {tone}. "
        )

        # 6) llamada al modelo
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # 7) ActionsEngine
        action_result = self.actions.handle(
            intent=intent,
            user_msg=user_msg,
            context=ctx,
            memory=self.memory
        )

        # 8) texto final
        final_answer = action_result.get("final") or raw_answer

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action_result.get("action")
        }
