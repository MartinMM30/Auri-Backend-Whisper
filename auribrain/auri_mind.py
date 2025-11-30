from openai import OpenAI

from auribrain.intent_engine import IntentEngine
from auribrain.memory_engine import MemoryEngine
from auribrain.context_engine import ContextEngine
from auribrain.personality_engine import PersonalityEngine
from auribrain.response_engine import ResponseEngine
from auribrain.actions_engine import AuriActionsEngine
from auribrain.entity_extractor import EntityExtractor


class AuriMind:
    """
    Núcleo de inteligencia de Auri.
    """

    def __init__(self):
        self.client = OpenAI()

        self.intent = IntentEngine(self.client)

        # Memoria
        self.memory = MemoryEngine()

        # Contexto
        self.context = ContextEngine()
        self.context.attach_memory(self.memory)

        # Estilo
        self.personality = PersonalityEngine()

        # Respuestas
        self.response = ResponseEngine()

        # FASE 9 — Extractor
        self.extractor = EntityExtractor(self.client)

        # FASE 10 — Acciones reales
        self.actions = AuriActionsEngine(self.extractor)

    # -------------------------------------------------------------
    # THINK — pipeline moderno
    # -------------------------------------------------------------
    def think(self, user_msg: str):
        if not user_msg.strip():
            return {
                "intent": "unknown",
                "raw": "",
                "final": "No logré escucharte, ¿puedes repetirlo?",
                "action": None
            }

        # 1) Guardar memoria
        self.memory.add_interaction(user_msg)

        # 2) Detectar intención
        intent = self.intent.detect(user_msg)

        # 3) Obtener contexto
        ctx = self.context.get_daily_context()

        # 4) Perfil final
        style = self.personality.build_final_style(
            context=ctx,
            emotion=self.memory.get_emotion()
        )

        # ---------------------------------------------------------
        # 5) SYSTEM PROMPT
        # ---------------------------------------------------------
        system_prompt = (
            "Eres Auri, un asistente personal cálido y cercano. "
            "Responde SIEMPRE en máximo 2 frases naturales. "
            "No repitas lo que dijo el usuario. "
            "No menciones tus tonos o rasgos internos. "
            "No describas tu razonamiento. "
            "No digas frases como 'estoy analizando', 'es una buena mañana', "
            "'recuerdo que antes dijiste', o similares. "
            "Responde directo, útil y humano."
        )

        # 6) LLM BASE
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
        )

        raw_answer = resp.output_text.strip()

        # 7) FASE 10 — Acciones
        action_result = self.actions.handle(
            intent=intent,
            text=user_msg
        )

        action = action_result.get("action")
        action_final_override = action_result.get("final")

        # 8) Determinar respuesta final
        final_answer = (
            action_final_override
            if action_final_override else
            self.response.build(
                intent=intent,
                style=style,
                context=ctx,
                memory=self.memory,
                user_msg=user_msg,
                raw_answer=raw_answer
            )
        )

        return {
            "intent": intent,
            "raw": raw_answer,
            "final": final_answer,
            "action": action
        }
